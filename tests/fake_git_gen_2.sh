rm -rf /tmp/tests_git
mkdir /tmp/tests_git
cd /tmp/tests_git
git init
echo "foo blabla" > foo
git add foo
echo "tata blabla" > tata
git add tata
git commit -m 'initial commit'

git checkout -b tmp

echo "toto blabla" > toto
git add toto
git commit -m 'adding toto'

git mv foo X
echo "tata bloblo" > toto
git rm tata
git commit -a -m 'rename foo to X, changing the content of toto, removing tata (rebase me to master)'

git checkout -
git mv foo Y
git commit -m 'rename foo to Y'
echo "other tata blabla" > tata
git commit -a -m 'changing the content of tata'
