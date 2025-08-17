test -f dataset/archive.zip || {
  mkdir -p dataset
  wget https://s3-eu-west-1.amazonaws.com/static.oc-static.com/prod/courses/files/Parcours_data_scientist/Projet+-+Impl%C3%A9menter+un+mod%C3%A8le+de+scoring/Projet+Mise+en+prod+-+home-credit-default-risk.zip -O dataset/archive.zip.tmp
  sha256sum -c <(echo '4aac489afc17bd09dd384fb232ef9da5e49d2d64ede6cc27fdd4efa3c4aad996  dataset/archive.zip.tmp') > /dev/null && {
    mv dataset/archive.zip.tmp -nv dataset/archive.zip
  } || {
    echo Download Failed
  }
}
test -f dataset/archive || {
  unzip dataset/archive.zip -d dataset/archive.tmp && mv -nv dataset/archive.tmp dataset/archive
}