# Newsletter Service
<p align="center">
<img src="https://cloud.githubusercontent.com/assets/3826929/23343971/615f90f0-fc74-11e6-83a8-fc09357e431e.png" title="Newsletter" width="640" />
</p>

Requires a `settings.ini` file:

```INI
[SMTP]
server: smtp.example.com
user: username
password: password
sender: newsletter@example.de

[Database]
file: addresses.txt
```
The file `addresses.txt` should contain one recipients email address per line:
```
email1@example.com
email2@example.com
email3@example.com
…
```
