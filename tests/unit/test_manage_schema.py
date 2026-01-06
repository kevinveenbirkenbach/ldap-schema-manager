import sys
import unittest
from unittest.mock import MagicMock, patch

import ldapsm.__main__ as manage_schema


class TestManageSchema(unittest.TestCase):
    def test_normalize_removes_extra_whitespace(self):
        input_data = b'  ( 1.2.3.4  NAME   \'foo\' \n DESC \t "bar" )  '
        expected = b'( 1.2.3.4 NAME \'foo\' DESC "bar" )'
        self.assertEqual(manage_schema.normalize(input_data), expected)

    def test_extract_oid_from_definition(self):
        ldif = "( 1.3.6.1.4.1.99999.1 NAME 'example' DESC 'something' )"
        oid = manage_schema.extract_oid(ldif)
        self.assertEqual(oid, "1.3.6.1.4.1.99999.1")

    @patch("ldapsm.__main__.ldap.initialize")
    def test_add_new_object_class_no_double_add(self, mock_ldap_init):
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn

        schema_name = "nextcloud"
        ocdef = "( 1.3.6.1.4.1.99999.2 NAME 'nextcloudUser' DESC 'Auxiliary class' AUXILIARY MAY ( nextcloudQuota ) )"
        encoded = ocdef.encode()

        mock_conn.search_s.side_effect = [
            [(f"cn={{0}}{schema_name},cn=schema,cn=config", {"dn": [b"dummy"]})],
            [(f"cn={{0}}{schema_name},cn=schema,cn=config", {"olcObjectClasses": [encoded]})],
        ]

        with patch.object(
            sys,
            "argv",
            [
                "ldapsm",
                "-s",
                "ldap://localhost",
                "-D",
                "cn=admin,dc=example,dc=org",
                "-W",
                "secret",
                "-n",
                schema_name,
                "-c",
                ocdef,
            ],
        ):
            manage_schema.main()

        mock_conn.modify_s.assert_not_called()

    @patch("ldapsm.__main__.ldap.initialize")
    def test_replace_attribute_type_same_oid(self, mock_ldap_init):
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn

        schema_name = "nextcloud"
        atdef = "( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Quota for Nextcloud' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )"
        encoded = atdef.encode()

        existing_attr_old = b"( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Old desc' SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 )"

        mock_conn.search_s.side_effect = [
            [(f"cn={{0}}{schema_name},cn=schema,cn=config", {"dn": [b"dummy"]})],
            [(f"cn={{0}}{schema_name},cn=schema,cn=config", {"olcAttributeTypes": [existing_attr_old]})],
        ]

        with patch.object(
            sys,
            "argv",
            [
                "ldapsm",
                "-s",
                "ldap://localhost",
                "-D",
                "cn=admin,dc=example,dc=org",
                "-W",
                "secret",
                "-n",
                schema_name,
                "-a",
                atdef,
            ],
        ):
            manage_schema.main()

        mock_conn.modify_s.assert_called_once()
        args, _kwargs = mock_conn.modify_s.call_args
        self.assertIn("cn={0}nextcloud,cn=schema,cn=config", args[0])
        self.assertEqual(args[1][0][0], manage_schema.ldap.MOD_REPLACE)
        self.assertEqual(args[1][0][1], "olcAttributeTypes")
        self.assertEqual(args[1][0][2], [encoded])


if __name__ == "__main__":
    unittest.main()
