# LDAP Schema Manager 🛠️

A Python-based CLI tool for managing OpenLDAP schema snippets under `cn=config`, allowing you to create or update schema entries—including custom `olcAttributeTypes` and `olcObjectClasses`—via LDAPI.

## 🚀 Installation

You can install **ldapsm** easily using [Kevin's package manager](https://github.com/kevinveenbirkenbach/package-manager):

```bash
pkgmgr install ldapsm
```

## 📝 Usage

After installation, run:

```bash
ldapsm --help
```

to view all available commands and options.

### Example

```bash
ldapsm \
  -s ldapi:/// \
  -D "" \
  -W "" \
  -n nextcloud \
  -a "( 1.3.6.1.4.1.99999.1 NAME 'nextcloudQuota' DESC 'Quota for Nextcloud' EQUALITY integerMatch ORDERING integerOrderingMatch SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )" \
  -c "( 1.3.6.1.4.1.99999.2 NAME 'nextcloudUser' DESC 'Auxiliary class for Nextcloud attributes' AUXILIARY MAY ( nextcloudQuota ) )"
```

## 📖 Help

For detailed usage and options, run:

```bash
ldapsm --help
```

## 🛡️ Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues](https://github.com/kevinveenbirkenbach/ldap-schema-manager/issues).

## 📜 License

This project is licensed under the MIT License.

---

**Author:** [Kevin Veen-Birkenbach](https://www.veen.world/)
