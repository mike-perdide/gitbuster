# This script generates a repository where cherry-picking the last commit of
# the tmp branch from the master branch will cause a merge conflict with
# every possible state of conflict represented:
#  * AA on Z
#  * AU on Y
#  * UA on X
#  * UU on jimmy
#  * DU on toto
#  * UD on tata
#  * DD on foo
 
rm -rf /tmp/tests_git
mkdir /tmp/tests_git
cd /tmp/tests_git
git init
echo "foo blabla" > foo
git add foo
echo "tata blabla" > tata
git add tata
echo "initial input" > jimmy
git add jimmy
git commit -m 'initial commit'

git checkout -b tmp

echo "toto blabla" > toto
git add toto
git commit -m 'adding toto'

git mv foo X
echo "tata bloblo" > toto
git rm tata
echo "Z tmp blabla" > Z
git add Z
echo "tmp input blabla" > jimmy
git commit -a -m "conflictable commit

rename foo to X, change the content of toto, remove tata, add Z, change the content of jimmy (rebase me to master)"

git checkout -
git mv foo Y
git commit -m 'rename foo to Y'

echo "Z blabla" > Z
git add Z
git ci -m "adding Z"

echo "other tata blabla" > tata
git commit -a -m 'changing the content of tata'

echo "master input blabla" > jimmy
git commit -a -m 'changing the content of jimmy'
