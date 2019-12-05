build:
	rm -fr lib/op
	$(eval TMPDIR := $(shell mktemp -d))
	wget https://github.com/canonical/operator/archive/master.zip -O $(TMPDIR)/master.zip
	unzip $(TMPDIR)/master.zip 'operator-master/op/*' -d $(TMPDIR)
	mv $(TMPDIR)/operator-master/op lib/op
	rm -rf $(TMPDIR)
clean:
	rm -fr lib/op
