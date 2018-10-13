
Use this repository to send email and a tweet when a Raspberry Pi boots. This is useful for general debugging and when your IP might change.

## Install tweepy (for tweets)

	pip3 install tweepy
	
## Install using `crontab -e`

```
@reboot (sleep 10; /usr/bin/python3 /home/pie/startupnotify/startuptweet.py booted)
@reboot (sleep 10; /usr/bin/python3 /home/pie/startupnotify/startupmailer.py booted)
```

## Configure

Create a file `my_config.py` and fill in some parameters.

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
cd ~/pie/startupnotify
python3 startupmailer.py 'my test worked'
python3 startuptweet.py 'my test tweet worked'
```
