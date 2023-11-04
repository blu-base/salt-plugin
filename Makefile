all: install

clean:
	rm -rf build

build:
	mkdir -p build/libs build/zip-content/salt-plugin
	cp -r contents resources plugin.yaml build/zip-content/salt-plugin
	sed -i \
		-e 's/@author@/Sebastian Engel/g' \
		-e 's/@name@/Salt Plugin/g' \
		-e 's/@description@/Plugins for SaltStack via its API/g' \
		build/zip-content/salt-plugin/plugin.yaml
	cd build/zip-content; zip -r salt-plugin.zip *
	mv build/zip-content/salt-plugin.zip build/libs

