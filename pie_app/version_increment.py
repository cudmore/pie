
import json, subprocess

import version

if __name__ == '__main__':
	version_json_file = 'version.json'
	
	with open(version_json_file) as inFile:
		version_json = json.load(inFile)
	print('old version_json:', version_json)
	
	"""
	# version_json looks like this
	{
	"major": "20190108",
	"minor": 169
	}
	"""
	
	# increment minor. This corresponds to each githb push
	version_json['minor'] += 1
	
	print('new version_json:', version_json)
	
	# save again
	with open(version_json_file, 'w') as outfile:
		json.dump(version_json, outfile, indent=4)
	
	
	okGo = True
	
	# commit to local git
	"""
	commitStr = 'xxx'
	cmd = ['git', 'commit', '-a', '-m', commitStr]
	try:
		commitOut = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		print('commitOut:', commitOut)
	except (subprocess.CalledProcessError) as e:
		print('git commit exception:', e)
		okGo = False
	"""
		
	# push to github
	"""
	if okGo:
		cmd = ['git', 'push']
		try:
			pushOut = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
		except (subprocess.CalledProcessError) as e:
			print('git push exception:', e)

		print('pushOut:', pushOut)
	"""