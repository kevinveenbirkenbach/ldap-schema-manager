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

def normalize(def_str: bytes) -> bytes:
    """
    Collapse all whitespace (Spaces, Newlines, Tabs) to single spaces,
    strip leading/trailing whitespace, for reliable byte-wise comparisons.
    """
    return re.sub(rb'\s+', b' ', def_str.strip())

def extract_oid(ldif: str) -> str:
    match = re.search(r'\(\s*([\d\.]+)', ldif)
    return match.group(1) if match else ''

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
  
    # Determine existing indices and detect if schema snippet already exists
    idx_re = re.compile(r'\{(\d+)\}([^,]+)')
    indices = []
    existing_idx = None
    for dn, _ in entries:
        m = idx_re.search(dn)
        if not m:
            continue
        idx = int(m.group(1))
        name = m.group(2)  # snippet name before the comma
        indices.append(idx)
        if name == args.schema_name:
            existing_idx = idx

    # Compute which index to use
    if existing_idx is not None:
        idx = existing_idx
        print(f"✔️  Using existing schema snippet {{{idx}}}{args.schema_name}")
    else:
        idx = max(indices) + 1 if indices else 0
        prefix = f'{{{idx}}}'
        new_dn = f"cn={prefix}{args.schema_name},{base_dn}"
        entry_attrs = {
            'objectClass': [b'top', b'olcSchemaConfig'],
            'cn': [f"{prefix}{args.schema_name}".encode()],
        }
        conn.add_s(new_dn, ldap.modlist.addModlist(entry_attrs))
        print(f"✅ Created new schema snippet: {new_dn}")

    # Final DN for modifications
    prefix = f'{{{idx}}}'
    schema_dn = f"cn={prefix}{args.schema_name},{base_dn}"

    # Add/update AttributeTypes
    for atdef in args.attribute_type:
        encoded = atdef.encode()

        try:
            result = conn.search_s(schema_dn, ldap.SCOPE_BASE,
                                   attrlist=['olcAttributeTypes'])
            existing = result[0][1].get('olcAttributeTypes', [])

            norm_existing = [normalize(v) for v in existing]
            norm_encoded  = normalize(encoded)
            oid = extract_oid(atdef)

            # Normalize existing
            if norm_encoded in norm_existing:
                print(f"ℹ️  AttributeType exists → REPLACE: {atdef}")
                conn.modify_s(schema_dn, [
                    (ldap.MOD_REPLACE, 'olcAttributeTypes', [encoded])
                ])
                print(f"🔄 Replaced AttributeType: {atdef}")
            elif any(oid in entry.decode() for entry in existing):
                print(f"⚠️  AttributeType with same OID ({oid}) exists → REPLACE: {atdef}")
                conn.modify_s(schema_dn, [
                    (ldap.MOD_REPLACE, 'olcAttributeTypes', [encoded])
                ])
                print(f"🔄 Replaced AttributeType (OID match): {atdef}")
            else:
                print(f"➕ AttributeType fehlt → ADD: {atdef}")
                conn.modify_s(schema_dn, [
                    (ldap.MOD_ADD, 'olcAttributeTypes', [encoded])
                ])
                print(f"➕ Added AttributeType: {atdef}")


        except ldap.LDAPError as e:
            print(f"❌ LDAP error for AttributeType '{atdef}': {e}", file=sys.stderr)
            sys.exit(1)

    # Add/update ObjectClasses
    for ocdef in args.object_class:
        encoded = ocdef.encode()
        try:
            result = conn.search_s(schema_dn, ldap.SCOPE_BASE,
                                attrlist=['olcObjectClasses'])
            existing = result[0][1].get('olcObjectClasses', [])
            norm_existing = [normalize(v) for v in existing]
            norm_encoded = normalize(encoded)

            if norm_encoded in norm_existing:
                print(f"✅ ObjectClass already up to date: {ocdef}")
                continue

            elif any(extract_oid(oc.decode()) == extract_oid(ocdef) for oc in existing):
                print(f"⚠️ ObjectClass with same OID exists, replacing...")
                to_delete = [oc for oc in existing if extract_oid(oc.decode()) == extract_oid(ocdef)]
                for oc in to_delete:
                    conn.modify_s(schema_dn, [(ldap.MOD_DELETE, 'olcObjectClasses', [oc])])
                conn.modify_s(schema_dn, [(ldap.MOD_ADD, 'olcObjectClasses', [encoded])])
                print(f"🔄 Replaced ObjectClass: {ocdef}")

            else:
                conn.modify_s(schema_dn, [
                    (ldap.MOD_ADD, 'olcObjectClasses', [encoded])
                ])
                print(f"➕ Added ObjectClass: {ocdef}")
        except ldap.LDAPError as e:
            print(f"❌  LDAP error for ObjectClass '{ocdef}': {e}", file=sys.stderr)
            sys.exit(3)


    conn.unbind_s()

if __name__ == '__main__':
    main()
