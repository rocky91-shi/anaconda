#
# Copyright (C) 2020  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Martin Kolman <mkolman@redhat.com>
#
import os
import tempfile

import unittest
from unittest.mock import patch, Mock, call

from dasbus.typing import *  # pylint: disable=wildcard-import

from pyanaconda.core import util
from pyanaconda.core.constants import RHSM_SYSPURPOSE_FILE_PATH, \
    THREAD_WAIT_FOR_CONNECTING_NM, SUBSCRIPTION_REQUEST_TYPE_USERNAME_PASSWORD, \
    SUBSCRIPTION_REQUEST_TYPE_ORG_KEY

from pyanaconda.modules.common.errors.subscription import UnregistrationError, \
    RegistrationError, SubscriptionError
from pyanaconda.modules.common.structures.subscription import SubscriptionRequest

from pyanaconda.core.subscription import check_system_purpose_set

from pyanaconda.ui.lib.subscription import SubscriptionPhase, \
    register_and_subscribe, unregister, org_keys_sufficient, \
    username_password_sufficient


class CheckSystemPurposeSetTestCase(unittest.TestCase):
    """Test the check_system_purpose_set helper function."""

    def check_system_purpose_set_test(self):
        """Test the check_system_purpose_set() helper function."""
        # system purpose set
        with tempfile.TemporaryDirectory() as sysroot:
            # create a dummy syspurpose file
            syspurpose_path = RHSM_SYSPURPOSE_FILE_PATH
            directory = os.path.split(syspurpose_path)[0]
            os.makedirs(util.join_paths(sysroot, directory))
            os.mknod(util.join_paths(sysroot, syspurpose_path))
            self.assertTrue(check_system_purpose_set(sysroot))

        # system purpose not set
        with tempfile.TemporaryDirectory() as sysroot:
            self.assertFalse(check_system_purpose_set(sysroot))


class AsynchronousRegistrationTestCase(unittest.TestCase):
    """Test the asynchronous registration/unregistration helper functions."""

    PASSWORD_REQUEST = {
        "type": get_variant(Str, SUBSCRIPTION_REQUEST_TYPE_USERNAME_PASSWORD),
        "organization": get_variant(Str, "123456789"),
        "account-username": get_variant(Str, "foo_user"),
        "server-hostname": get_variant(Str, "candlepin.foo.com"),
        "rhsm-baseurl": get_variant(Str, "cdn.foo.com"),
        "server-proxy-hostname": get_variant(Str, "proxy.foo.com"),
        "server-proxy-port": get_variant(Int, 9001),
        "server-proxy-user": get_variant(Str, "foo_proxy_user"),
        "account-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")}),
        "activation-keys":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(List[Str], [])}),
        "server-proxy-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")})
    }

    PASSWORD_MISSING_REQUEST = {
        "type": get_variant(Str, SUBSCRIPTION_REQUEST_TYPE_USERNAME_PASSWORD),
        "organization": get_variant(Str, "123456789"),
        "account-username": get_variant(Str, "foo_user"),
        "server-hostname": get_variant(Str, "candlepin.foo.com"),
        "rhsm-baseurl": get_variant(Str, "cdn.foo.com"),
        "server-proxy-hostname": get_variant(Str, "proxy.foo.com"),
        "server-proxy-port": get_variant(Int, 9001),
        "server-proxy-user": get_variant(Str, "foo_proxy_user"),
        "account-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "NONE"),
                         "value": get_variant(Str, "")}),
        "activation-keys":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(List[Str], [])}),
        "server-proxy-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")})
    }

    KEY_REQUEST = {
        "type": get_variant(Str, SUBSCRIPTION_REQUEST_TYPE_ORG_KEY),
        "organization": get_variant(Str, "123456789"),
        "account-username": get_variant(Str, "foo_user"),
        "server-hostname": get_variant(Str, "candlepin.foo.com"),
        "rhsm-baseurl": get_variant(Str, "cdn.foo.com"),
        "server-proxy-hostname": get_variant(Str, "proxy.foo.com"),
        "server-proxy-port": get_variant(Int, 9001),
        "server-proxy-user": get_variant(Str, "foo_proxy_user"),
        "account-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")}),
        "activation-keys":
            get_variant(Structure,
                        {"type": get_variant(Str, "TEXT"),
                         "value": get_variant(List[Str], [])}),
        "server-proxy-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")})
    }

    KEY_MISSING_REQUEST = {
        "type": get_variant(Str, SUBSCRIPTION_REQUEST_TYPE_ORG_KEY),
        "organization": get_variant(Str, "123456789"),
        "account-username": get_variant(Str, "foo_user"),
        "server-hostname": get_variant(Str, "candlepin.foo.com"),
        "rhsm-baseurl": get_variant(Str, "cdn.foo.com"),
        "server-proxy-hostname": get_variant(Str, "proxy.foo.com"),
        "server-proxy-port": get_variant(Int, 9001),
        "server-proxy-user": get_variant(Str, "foo_proxy_user"),
        "account-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")}),
        "activation-keys":
            get_variant(Structure,
                        {"type": get_variant(Str, "NONE"),
                         "value": get_variant(List[Str], [])}),
        "server-proxy-password":
            get_variant(Structure,
                        {"type": get_variant(Str, "HIDDEN"),
                         "value": get_variant(Str, "")})
    }

    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def org_keys_sufficient_test(self, get_proxy):
        """Test the org_keys_sufficient() helper method."""
        subscription_proxy = get_proxy.return_value
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_REQUEST
        # run the function
        self.assertTrue(org_keys_sufficient())

    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def org_keys_sufficient_not_sufficient_test(self, get_proxy):
        """Test the org_keys_sufficient() helper method - not sufficient."""
        subscription_proxy = get_proxy.return_value
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_MISSING_REQUEST
        # run the function
        self.assertFalse(org_keys_sufficient())

    def org_keys_sufficient_direct_request_test(self):
        """Test the org_keys_sufficient() helper method - direct request."""
        # run the function with sufficient authentication data
        request = SubscriptionRequest.from_structure(self.KEY_REQUEST)
        self.assertTrue(org_keys_sufficient(subscription_request=request))
        # run the function with insufficient authentication data
        request = SubscriptionRequest.from_structure(self.KEY_MISSING_REQUEST)
        self.assertFalse(org_keys_sufficient(subscription_request=request))


    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def username_password_sufficient_test(self, get_proxy):
        """Test the username_password_sufficient() helper method."""
        subscription_proxy = get_proxy.return_value
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_REQUEST
        # run the function
        self.assertTrue(username_password_sufficient())

    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def username_password_sufficient_not_sufficient_test(self, get_proxy):
        """Test the username_password_sufficient() helper method - not sufficient."""
        subscription_proxy = get_proxy.return_value
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_MISSING_REQUEST
        # run the function
        self.assertFalse(username_password_sufficient())

    def username_password_sufficient_direct_request_test(self):
        """Test the username_password_sufficient() helper method - direct request."""
        # run the function with sufficient authentication data
        request = SubscriptionRequest.from_structure(self.PASSWORD_REQUEST)
        self.assertTrue(username_password_sufficient(subscription_request=request))
        # run the function with insufficient authentication data
        request = SubscriptionRequest.from_structure(self.PASSWORD_MISSING_REQUEST)
        self.assertFalse(username_password_sufficient(subscription_request=request))

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_org_key_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - org & key."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_REQUEST
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # system was no registered, so no unregistration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER),
             call(SubscriptionPhase.ATTACH_SUBSCRIPTION),
             call(SubscriptionPhase.DONE)]
        )
        # we were successful, so no error callback calls
        error_callback.assert_not_called()
        # we should have requested the appropriate tasks
        subscription_proxy.RegisterOrganizationKeyWithTask.assert_called_once()
        subscription_proxy.AttachSubscriptionWithTask.assert_called_once()
        subscription_proxy.ParseAttachedSubscriptionsTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_username_password_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - username & password."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_REQUEST
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # system was no registered, so no unregistration phase
        print(error_callback.mock_calls)
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER),
             call(SubscriptionPhase.ATTACH_SUBSCRIPTION),
             call(SubscriptionPhase.DONE)]
        )
        # we were successful, so no error callback calls
        error_callback.assert_not_called()
        # we should have requested the appropriate tasks
        subscription_proxy.RegisterUsernamePasswordWithTask.assert_called_once()
        subscription_proxy.AttachSubscriptionWithTask.assert_called_once()
        subscription_proxy.ParseAttachedSubscriptionsTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def unregister_register_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - registered system."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system being registered,
        # - this should add additional unregister phase and task
        subscription_proxy.IsRegistered = True
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_REQUEST
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # check the phases and their order
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.UNREGISTER),
             call(SubscriptionPhase.REGISTER),
             call(SubscriptionPhase.ATTACH_SUBSCRIPTION),
             call(SubscriptionPhase.DONE)]
        )
        # we were successful, so no error callback calls
        error_callback.assert_not_called()
        # we should have requested the appropriate tasks
        subscription_proxy.UnregisterWithTask.assert_called_once()
        subscription_proxy.RegisterOrganizationKeyWithTask.assert_called_once()
        subscription_proxy.AttachSubscriptionWithTask.assert_called_once()
        subscription_proxy.ParseAttachedSubscriptionsTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def unregister_task_failed_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - unregistration failed."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system being registered,
        # - this should add additional unregister phase and task
        subscription_proxy.IsRegistered = True
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_REQUEST
        # make the first (unregistration) task fail
        run_task.side_effect = [UnregistrationError("unregistration failed")]
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the unregistration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.UNREGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once_with("unregistration failed")
        # we should have requested the appropriate tasks
        subscription_proxy.UnregisterWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_org_key_task_failed_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - org & key failed."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_REQUEST
        # make the first (registration) task fail
        run_task.side_effect = [RegistrationError("registration failed")]
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the registration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once_with("registration failed")
        # we should have requested the appropriate tasks
        subscription_proxy.RegisterOrganizationKeyWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_key_missing_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - key missing."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.KEY_MISSING_REQUEST
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the registration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once()
        # int this case we fails before requesting any task and we should not
        # attempt to run any
        run_task.assert_not_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_username_password_task_failed_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - username & password failed."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_REQUEST
        # make the first (registration) task fail
        run_task.side_effect = [RegistrationError("registration failed")]
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the registration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once_with("registration failed")
        # we should have requested the appropriate tasks
        subscription_proxy.RegisterUsernamePasswordWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def register_password_missing_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - password missing."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_MISSING_REQUEST
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the registration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once()
        # int this case we fails before requesting any task and we should not
        # attempt to run any
        run_task.assert_not_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.threading.threadMgr.wait")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def attach_subscription_task_failed_test(self, get_proxy, thread_mgr_wait, run_task):
        """Test the register_and_subscribe() helper method - failed to attach subscription."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system not being registered
        subscription_proxy.IsRegistered = False
        # simulate subscription request
        subscription_proxy.SubscriptionRequest = self.PASSWORD_REQUEST
        # make the second (subscription) task fail
        run_task.side_effect = [True, SubscriptionError("failed to attach subscription")]
        # run the function
        register_and_subscribe(progress_callback=progress_callback,
                               error_callback=error_callback)
        # we should have waited on network
        thread_mgr_wait.assert_called_once_with(THREAD_WAIT_FOR_CONNECTING_NM)
        # there should be only the registration & subscription phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.REGISTER),
             call(SubscriptionPhase.ATTACH_SUBSCRIPTION)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once_with("failed to attach subscription")
        # we should have requested the appropriate tasks
        subscription_proxy.RegisterUsernamePasswordWithTask.assert_called_once()
        subscription_proxy.AttachSubscriptionWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def unregister_test(self, get_proxy, run_task):
        """Test the unregister() helper method."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system being registered,
        subscription_proxy.IsRegistered = True
        # run the function
        unregister(progress_callback=progress_callback,
                   error_callback=error_callback)
        # there should be the unregistration & done phases
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.UNREGISTER),
             call(SubscriptionPhase.DONE)]
        )
        # the error callback should not have been called
        error_callback.assert_not_called()
        # we should have requested the appropriate tasks
        subscription_proxy.UnregisterWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def unregister_not_registered_test(self, get_proxy, run_task):
        """Test the unregister() helper method - not registered."""
        # this is effectively a no-op
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system being registered,
        subscription_proxy.IsRegistered = False
        # run the function
        unregister(progress_callback=progress_callback,
                   error_callback=error_callback)
        # there should be just the done phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.DONE)]
        )
        # the error callback should not have been called
        error_callback.assert_not_called()
        # no need to request and run any tasks
        run_task.assert_not_called()

    @patch("pyanaconda.modules.common.task.sync_run_task")
    @patch("pyanaconda.modules.common.constants.services.SUBSCRIPTION.get_proxy")
    def unregister_failed_test(self, get_proxy, run_task):
        """Test the unregister() helper method - unregistration failed."""
        progress_callback = Mock()
        error_callback = Mock()
        subscription_proxy = get_proxy.return_value
        # simulate the system being registered,
        subscription_proxy.IsRegistered = True
        # make the unregistration task fail
        run_task.side_effect = [UnregistrationError("unregistration failed")]
        # run the function
        unregister(progress_callback=progress_callback,
                   error_callback=error_callback)
        # there should be only the unregistration phase
        progress_callback.assert_has_calls(
            [call(SubscriptionPhase.UNREGISTER)]
        )
        # and the error callback should have been triggered
        error_callback.assert_called_once_with("unregistration failed")
        # we should have requested the appropriate tasks
        subscription_proxy.UnregisterWithTask.assert_called_once()
        # and tried to run them
        run_task.assert_called()
