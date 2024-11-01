deploy:
	ssh life.unbl.ink "rm -rf /root/vrobbler-venv/lib/python3.11/site-packages/vrobbler-0.15.4.dist-info/ && pip install git+https://code.unbl.ink/secstate/vrobbler.git@develop && systemctl restart vrobbler"
logs:
	ssh life.unbl.ink tail -n 100 -f /var/log/vrobbler.json
