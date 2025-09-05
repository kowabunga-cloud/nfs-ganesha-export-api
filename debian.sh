#!/bin/bash

VERSION=$(cat setup.py | grep version | sed "s%.*version='\(.*\)',%\1%g")

export CURRENT_VERSION=$(git tag --sort=-committerdate | head -1)
export PREVIOUS_VERSION=$(git tag --sort=-committerdate | head -2 | awk '{split($0, tags, "\n")} END {print tags[1]}')
export CHANGES=$(git log --pretty="- %s" $CURRENT_VERSION...$PREVIOUS_VERSION)
[ -z "$CHANGES" ] && CHANGES="- Initial release"

cat > debian/changelog <<EOF
nfs-ganesha-export-api (${VERSION}) unstable; urgency=medium

${CHANGES}

 -- The Kowabunga Project <maintainers@kowabunga.cloud>  $(date -R)
EOF

sed -i 's%^-%  \*%g' debian/changelog
sudo mk-build-deps --install --tool='apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes' debian/control
fakeroot debian/rules binary
