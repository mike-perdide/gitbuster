rm -rf /tmp/tests_git
mkdir /tmp/tests_git
cd /tmp/tests_git

export GIT_COMMITTER_NAME="Committer Groom"
export GIT_COMMITTER_EMAIL="committer@groom.com"

export GIT_AUTHOR_NAME="Author 'Master' Groom"
export GIT_AUTHOR_EMAIL="author-master@groom.com"

git init
echo "init" > file1
git add file1
git commit -a -m "Initial commit"
git branch wallace_branch
git co wallace_branch

export GIT_AUTHOR_NAME="Author 'Wallace' Groom"
export GIT_AUTHOR_EMAIL="author-wallace@groom.com"

echo "rooh" > file1
git commit -a -m "Added rooh to file1 (was empty)"
echo "hello" > file1
git commit -a -m "Replaced rooh with hello in file1"
echo "cardboard" > file1
git commit -a -m "Replaced hello with cardboard in file1"

git co master

export GIT_AUTHOR_NAME="Author 'Master' Groom"
export GIT_AUTHOR_EMAIL="author-master@groom.com"

echo "okay" > file1
git commit -a -m "Added okay to file1 (was empty)"
echo "hello" > file1
git commit -a -m "Replaced okay with hello in file1"
echo "bobby" > file1
git commit -a -m "Replaced hello with bobby in file1"

echo "troutman" > file2
git add file2
git commit -a -m "Adding file2"
echo "flint" > file2
git commit -a -m "Replaced troutman with flint in file2"
echo "rodney" > file2
echo "jimmy" > file1
git commit -a -m "Replaced flint with rodney in file2 and bobby with jimmy in file1"
git rm file2
echo "scourge" > file1
git commit -a -m "Removing file2 and replaced jimmy with scourge in file1"
