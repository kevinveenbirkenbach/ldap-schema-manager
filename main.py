#!/usr/bin/env python3
"""
manage_schema.py — Create or update OpenLDAP schema snippets under cn=schema,cn=config.

Usage example:

  ./manage_schema.py \
    -s ldapi:/// \
    -D "" \
    -W "" \
    -n nextcloud \
    -a "( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Quota for Nextcloud' EQUALITY integerMatch ORDERING integerOrderingMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )" \
    -c "( 1.3.6.1.4.1.99999.2 NAME 'nextcloudUser' DESC 'Auxiliary class for Nextcloud attributes' AUXILIARY MAY ( nextcloudQuota ) )"
"""

import ldap
import ldap.modlist as modlist
import argparse
import re
import sys

def main():
    parser = argparse.ArgumentParser(
        description='Create or update OpenLDAP schema entries under cn=config'
    )
    parser.add_argument(
        '-s', '--server-uri',
        default='ldapi:///',
        help='LDAP server URI (default: ldapi:///)'
    )
    parser.add_argument(
        '-D', '--bind-dn',
        default='',
        help='Bind DN (empty for SASL EXTERNAL)'
    )
    parser.add_argument(
        '-W', '--bind-pw',
        default='',
        help='Bind password'
    )
    parser.add_argument(
        '-n', '--schema-name',
        required=True,
        help='Schema snippet name (e.g. nextcloud)'
    )
    parser.add_argument(
        '-a', '--attribute-type',
        action='append',
        default=[],
        help='AttributeType definition in LDIF syntax (can be given multiple times)'
    )
    parser.add_argument(
        '-c', '--object-class',
        action='append',
        default=[],
        help='ObjectClass definition in LDIF syntax (can be given multiple times)'
    )
    parser.add_argument(
        '--attrs-file',
        help='File containing AttributeType definitions, one per line'
    )
    parser.add_argument(
        '--objs-file',
        help='File containing ObjectClass definitions, one per line'
    )
    args = parser.parse_args()

    # Load definitions from files if given
    if args.attrs_file:
        try:
            with open(args.attrs_file) as f:
                args.attribute_type.extend(
                    line.strip() for line in f if line.strip()
                )
        except Exception as e:
            print(f"Error reading attrs file: {e}", file=sys.stderr)
            sys.exit(1)
    if args.objs_file:
        try:
            with open(args.objs_file) as f:
                args.object_class.extend(
                    line.strip() for line in f if line.strip()
                )
        except Exception as e:
            print(f"Error reading objs file: {e}", file=sys.stderr)
            sys.exit(1)

    if not args.attribute_type and not args.object_class:
        print("No attributeType or objectClass definitions provided.", file=sys.stderr)
        sys.exit(1)

    # Connect & bind
    try:
        conn = ldap.initialize(args.server_uri)
        conn.simple_bind_s(args.bind_dn, args.bind_pw)
    except ldap.LDAPError as e:
        print(f"LDAP bind failed: {e}", file=sys.stderr)
        sys.exit(1)

    base_dn = 'cn=schema,cn=config'

    # Fetch existing schema entries
    try:
        entries = conn.search_s(
            base_dn,
            ldap.SCOPE_ONELEVEL,
            '(objectClass=olcSchemaConfig)',
            ['dn']
        )
    except ldap.LDAPError as e:
        print(f"Failed to search schema container: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine existing indices
    idx_pattern = re.compile(r'\{(\d+)\}(.+)')
    indices = []
    existing_idx = None
    for dn, _ in entries:
        m = idx_pattern.search(dn)
        if m:
            idx = int(m.group(1))
            name = m.group(2)
            indices.append(idx)
            if name == args.schema_name:
                existing_idx = idx

    # Compute target index
    if existing_idx is not None:
        idx = existing_idx
        print(f"Using existing schema index {{idx}} for '{args.schema_name}'")
    else:
        idx = (max(indices) + 1) if indices else 0
        prefix = f'{{{idx}}}'
        new_dn = f"cn={prefix}{args.schema_name},{base_dn}"
        entry_attrs = {
            'objectClass': [b'top', b'olcSchemaConfig'],
            'cn': [f"{prefix}{args.schema_name}".encode()],
        }
        ldif = modlist.addModlist(entry_attrs)
        try:
            conn.add_s(new_dn, ldif)
            print(f"Created schema entry {new_dn}")
        except ldap.LDAPError as e:
            print(f"Failed to create schema entry: {e}", file=sys.stderr)
            sys.exit(1)

    # Final DN for modifications
    prefix = f'{{{idx}}}'
    schema_dn = f"cn={prefix}{args.schema_name},{base_dn}"

    # Add/update AttributeTypes
    for atdef in args.attribute_type:
        try:
            result = conn.search_s(schema_dn, ldap.SCOPE_BASE, attrlist=['olcAttributeTypes'])
            existing = result[0][1].get('olcAttributeTypes', [])
            encoded = atdef.encode()
            if encoded in existing:
                print(f"AttributeType already present: {atdef}")
            else:
                conn.modify_s(schema_dn, [(ldap.MOD_ADD, 'olcAttributeTypes', [encoded])])
                print(f"Added AttributeType: {atdef}")
        except ldap.LDAPError as e:
            print(f"Error adding AttributeType '{atdef}': {e}", file=sys.stderr)

    # Add/update ObjectClasses
    for ocdef in args.object_class:
        try:
            result = conn.search_s(schema_dn, ldap.SCOPE_BASE, attrlist=['olcObjectClasses'])
            existing = result[0][1].get('olcObjectClasses', [])
            encoded = ocdef.encode()
            if encoded in existing:
                print(f"ObjectClass already present: {ocdef}")
            else:
                conn.modify_s(schema_dn, [(ldap.MOD_ADD, 'olcObjectClasses', [encoded])])
                print(f"Added ObjectClass: {ocdef}")
        except ldap.LDAPError as e:
            print(f"Error adding ObjectClass '{ocdef}': {e}", file=sys.stderr)

    conn.unbind_s()

if __name__ == '__main__':
    main()
