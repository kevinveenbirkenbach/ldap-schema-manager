# LDAP Schema Manager 🛠️
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-blue?logo=github)](https://github.com/sponsors/kevinveenbirkenbach) [![Patreon](https://img.shields.io/badge/Support-Patreon-orange?logo=patreon)](https://www.patreon.com/c/kevinveenbirkenbach) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20Coffee-Funding-yellow?logo=buymeacoffee)](https://buymeacoffee.com/kevinveenbirkenbach) [![PayPal](https://img.shields.io/badge/Donate-PayPal-blue?logo=paypal)](https://s.veen.world/paypaldonate)

A Python-based CLI tool for managing OpenLDAP schema snippets under `cn=config`, allowing you to create or update schema entries—including custom `olcAttributeTypes` and `olcObjectClasses`—via LDAPI.

## 🚀 Installation (PyPI)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install ldapsm
```

### System dependencies (required for python-ldap)

`python-ldap` requires OpenLDAP development headers and SASL/SSL libraries.

Debian / Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  gcc python3-dev libldap2-dev libsasl2-dev libssl-dev
```

Arch Linux:

```bash
sudo pacman -S --needed gcc openldap
```

## 📝 Usage

After installation, run:

```bash
ldapsm --help
```

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
