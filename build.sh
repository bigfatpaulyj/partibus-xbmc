mkdir script.partibus
mkdir script.partibus/resources
cp default.py script.partibus/
cp addon.xml script.partibus/
cp -r resources/settings.xml script.partibus/resources/
zip dist.zip -r script.partibus/
echo "Build successful"
