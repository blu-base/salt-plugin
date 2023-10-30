all: install

clean:
	rm -rf build

build:
	mkdir -p build/libs build/zip-content/salt-plugin
	cp -r contents resources plugin.yaml build/zip-content/salt-plugin
	cd build/zip-content; zip -r salt-plugin.zip *
	mv build/zip-content/salt-plugin.zip build/libs

