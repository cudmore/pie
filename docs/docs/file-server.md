This is a recipe for configuring a Raspberry Pi as a file-server. Once configured as a file-server, files on the Raspberry Pi can be easily opened/edited/copied from a remote computer. This is useful for copying recorded video off the Raspberry Pi to another (remote) computer for archiving and analysis.

If you are working on a Windows machine, you need to use [Samba][samba]. If you are working on macOS you want to use [AFP][afp] but can also use [Samba][samba].


## Samba (SMB)

This is a recipe to make a Raspberry Pi a [Samba][samba] (SMB) file-server that can be accessed from both Windows and macOS.

### 1) Install Samba

    sudo apt-get install samba samba-common-bin

### 2) Edit `/etc/samba/smb.conf`

	sudo pico /etc/samba/smb.conf

When using the [`pico`][pico] editor, `ctrl+x` to save and quit, `ctrl+w` to search, `ctrl+v` to page down. Remember, the `pico` editor does not respond to mouse clicks, you need to move the cursor around with arrow keys.

### 3) Add the following to the end of the `smb.conf` file.

In the Pico editor, move the cursor to the end of the file and copy and paste the following.

	[video]
	Comment = Pi video shared folder
	Path = /home/pi/video
	Browseable = yes
	Writeable = yes
	only guest = no
	create mask = 0777
	directory mask = 0777
	Public = yes
	Guest ok = no

	[home]
	Comment = Pi shared folder
	Path = /home/pi
	Browseable = yes
	Writeable = yes
	only guest = no
	create mask = 0777
	directory mask = 0777
	Public = yes
	Guest ok = no

### 4) Create a Samba password

	sudo smbpasswd -a pi

### 5) Restart Samba

	sudo /etc/init.d/samba restart
	
### 6) Test the server from another machine on the network.

On a Windows machine, mount the Raspberry Pi Samba file-server with `smb:\\[piIP]` where [piIP] is the IP address of your pi. Do this by clicking the 'Start' menu and then typing `smb:\\[piIP]`.


## Apple-File-Protocol (AFP)

This is a recipe to make a Raspberry Pi an [Apple-File-Protocol][afp] (AFP) file-server that can be accessed from macOS.

### 1) Install netatalk

```
sudo apt-get install netatalk
```

Once netatalk is installed, the Raspberry Pi will show up in the macOS Finder 'Shared' section. The Pi can be mounted in the macOS Finder by going to `Go - Connect To Server...` and entering `afp://[piIP]` where [piIP] is the IP address of your Pi.

### 2) Changing the default name of a Pi in netatalk

When a Pi is mounted in macOS using AFP, it will mount as `Home Directory`. If you have multiple Raspberry Pi computers they all mount with the same 'Home Directory' name which can be confusing. Thus, you want to change the 'mount point' name of each Raspberry Pi. For more information, see [this blog post][afpmountpoint] to change the name of the mount point from 'Home Directory'. Or just follow along ...

Stop netatalk

```
sudo /etc/init.d/netatalk stop
```

Edit the netatalk config file

```
sudo pico /etc/netatalk/AppleVolumes.default
```

When using the [`pico`][pico] editor, `ctrl+x` to save and quit, `ctrl+w` to search, `ctrl+v` to page down. Remember, the `pico` editor does not respond to mouse clicks, you need to move the cursor around with arrow keys.

Scroll to the bottom of the file and change this one line where 'the_name_you_want' should be the name you want the given Raspberry Pi to mount as. The '#' is used as a comment and is ignored.

```
# By default all users have access to their home directories.
#~/                     "Home Directory"
~/                      "the_name_you_want"
```

### 3) Restart netatalk

```
sudo /etc/init.d/netatalk start
```

### 4) Test the server from another machine on the network.

In the macOS Finder, go to `Go - Connect To Server...` and enter `afp://[piIP]` where [piIP] is the IP address of your Pi.

[afpmountpoint]: http://blog.cudmore.io/post/2015/06/07/Changing-default-mount-in-Apple-File-Sharing/
[samba]: https://www.samba.org/
[afp]: http://netatalk.sourceforge.net/
[pico]: https://en.wikipedia.org/wiki/Pico_(text_editor)
