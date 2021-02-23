### Demo

<img src="https://user-images.githubusercontent.com/19658/108788304-02b9d780-75bb-11eb-96ed-8d76e3a37db2.gif" width=500>

### Slack App Settings

* App Home
  * Enable Home Tab
* Interactivity & Shortcuts
  * Message shortcut (callback_id: `send-this-message-later`)
* Events API
  * Bot events
    * `app_home_opened`
    * `app_uninstalled`
  * Events on behalf of users
    * `token_revoked`
* OAuth & Permissions
  * Bot Token Scopes
    * `commands`
    * `users:read`
  * User Token Scopes
    * `chat:write`
    * `users:read`
  * Redirect URLs
    * `https://{your domain}/slack/oauth_redirect`
* Beta Features
  * Opt into `timepicker`

### Local dev

```bash
cp _env .env  # and then, edit it
docker-compose up --build
docker-compose exec web python ./db_migration.py
ngrok http 3000 # for OAuth flow
```

### Heroku Deployment

```bash
heroku create

heroku addons:create heroku-postgresql:hobby-dev
aws s3 cp initial.dump s3://{your bucket}/initial.dump
aws s3 presign s3://{your bucket}/initial.dump
heroku pg:backups:restore ${presign url} DATABASE_URL

heroku config:set SLACK_CLIENT_ID=
heroku config:set SLACK_CLIENT_SECRET=
heroku config:set SLACK_SIGNING_SECRET=
heroku config:set SLACK_SCOPES=commands,users:read
heroku config:set SLACK_USER_SCOPES=chat:write,users:read

git add . -v
git commit -m'initial'
git push heroku main
```