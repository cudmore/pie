
Use this repository to send email and a tweet when a Raspberry Pi boots. This is useful for general debugging and when your IP might change.

## To send tweets

To send tweets you must have a normal twitter account and than apply for a twitter development account. See the [twitter apps page at apps.twitter.com](https://apps.twitter.com/) to apply for a development account. Once you have a development account you need to create an app and then you can access your developer keys allowing you to send tweets.

The `startuptweet.py` code uses [tweepy](http://www.tweepy.org/)

	pip3 install tweepy

## To send email

You can create an email account with gmail for this purpose. It is not the best idea to use your primary email account as the password is stored as plain text.

## Configure

First you want to copy the `startupnotify/` folder into your home directory.

	cd ~/pie
	cp -r startupnotify ~/
	
Create a file `my_config.py` and fill in some parameters. This file is read by both `startupmailer.py` and `startuptweet.py`.

```
pico ~/startupnotify/my_config.py
```

```
#
# tweet
hash_tag = '#my_hash_tag'
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

#
# email
# Change to your own account information to send from
gmail_user = 'sender@example.com'
gmail_password = 'sender_password'

# list of email accounts to send to
gmail_to = ['recipient@example.com']
```

## Testing

```
cd ~/startupnotify
python3 startupmailer.py 'my test email worked'
python3 startuptweet.py 'my test tweet worked'
```

## To tweet and email at boot

Use `crontab -e` and append these lines to your crontab file.

```
@reboot (sleep 10; /usr/bin/python3 /home/pi/startupnotify/startuptweet.py booted)
@reboot (sleep 10; /usr/bin/python3 /home/pi/startupnotify/startupmailer.py booted)
```

