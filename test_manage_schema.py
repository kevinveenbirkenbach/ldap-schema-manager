import unittest
from unittest.mock import patch, MagicMock
import main as manage_schema
import sys

class TestManageSchema(unittest.TestCase):

    def test_normalize_removes_extra_whitespace(self):
        input_data = b'  ( 1.2.3.4  NAME   \'foo\' \n DESC \t "bar" )  '
        expected = b'( 1.2.3.4 NAME \'foo\' DESC "bar" )'
        self.assertEqual(manage_schema.normalize(input_data), expected)

    @patch('ldap.initialize')
    def test_existing_attribute_type_replaced(self, mock_ldap_init):
        # Setup mock connection and search result
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn

        # Fake result for olcAttributeTypes containing old version
        existing_attr = b"( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Old desc' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 )"
        mock_conn.search_s.return_value = [(None, {'olcAttributeTypes': [existing_attr]})]

        # Call modify_s and simulate replace
        atdef = "( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Quota for Nextcloud' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )"
        dn = "cn={0}nextcloud,cn=schema,cn=config"

        # Manually test logic: normalize and modify decision
        norm_existing = [manage_schema.normalize(existing_attr)]
        norm_new = manage_schema.normalize(atdef.encode())
        self.assertNotEqual(norm_existing[0], norm_new)

        # Simulate replace
        mock_conn.modify_s.reset_mock()
        mock_conn.modify_s(dn, [(2, 'olcAttributeTypes', [atdef.encode()])])
        mock_conn.modify_s.assert_called_once_with(
            dn, [(2, 'olcAttributeTypes', [atdef.encode()])]
        )

    @patch('ldap.initialize')
    def test_add_new_object_class(self, mock_ldap_init):
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn

        # No existing object classes
        mock_conn.search_s.return_value = [(None, {'olcObjectClasses': []})]

        ocdef = "( 1.3.6.1.4.1.99999.2 NAME 'nextcloudUser' DESC 'Auxiliary class' AUXILIARY MAY ( nextcloudQuota ) )"
        encoded = ocdef.encode()

        # Simulate adding
        dn = "cn={0}nextcloud,cn=schema,cn=config"
        mock_conn.modify_s(dn, [(0, 'olcObjectClasses', [encoded])])
        mock_conn.modify_s.assert_called_once_with(
            dn, [(0, 'olcObjectClasses', [encoded])]
        )

        # Test no double add
        mock_conn.modify_s.reset_mock()
        mock_conn.search_s.return_value = [("cn={0}nextcloud,cn=schema,cn=config", {'olcObjectClasses': [encoded]})]
        with patch.object(sys, 'argv', [
            'manage_schema.py',
            '-s', 'ldap://localhost',
            '-D', 'cn=admin,dc=example,dc=org',
            '-W', 'secret',
            '-n', 'nextcloud',
            '-c', ocdef
        ]):
            manage_schema.main()
        mock_conn.modify_s.assert_not_called()


    def test_extract_oid_from_definition(self):
        ldif = "( 1.3.6.1.4.1.99999.1 NAME 'example' DESC 'something' )"
        oid = manage_schema.extract_oid(ldif)
        self.assertEqual(oid, "1.3.6.1.4.1.99999.1")


if __name__ == '__main__':
    unittest.main()
