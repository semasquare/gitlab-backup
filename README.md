# gitlab-backup

# Installation on Synology DiscStation

Create GitLab Token with scope `api`:

https://gitlab.com/-/user_settings/personal_access_tokens

Add token and other contents to .env:

```shell
cp .env.sample .env
```

Install Python on http://nas.local:

Open Package Center and install python.

Install pip:

Login via ssh and run the following commands:

```shell
sudo python3 -m ensurepip
sudo python3 -m pip install --upgrade pip
python3 -m pip -V
```

Install python3 venv:

```shell
python3 -m venv /Scripts/gitlab-backup
cd /volume1/Scripts/gitlab-backup
source bin/active
```

Install dependencies:

```shell
cd /volume1/Scripts/gitlab-backup
python3 -m pip install -r requirements.txt
```

Create Task with user defined script on http://nas.local:

```
/usr/bin/python3 /volume1/Backup/gitlab.com/gitlab-backup.py
```

# Usage

```shell
docker run -it --init --env-file .env -v "./data:/app/data" com.semasquare.gitlab-backup
```
