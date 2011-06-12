# master
#   *           Merge ABC123
#   |\
#   | *         Merge ABC (conflicts)
#   | |\
#   | | *       A (1')
#   | | *       B (2')
#   | | *       C (3')
#   | * |       1
#   | * |       2
#   | * |       3
#   * | |       T
#   * | |       U
#   * | |       V
#   |/ /
#   * /         X
#   |/
#   *           Initial commit

rm -rf /tmp/tests_git
mkdir /tmp/tests_git
cd /tmp/tests_git
git init

echo "initial" > initial
git add initial
git commit -m "Initial commit"

git checkout -b ABC
git checkout -

echo "X" > X
git add X
git commit -m "X"

git checkout -b 123
git checkout -

# Filling subtree TUV
echo "V" > V
git add V
git commit -m "V"

echo "U" > U
git add U
git commit -m "U"

echo "T" > T
git add T
git commit -m "T"

# Filling subtree 123
git checkout 123

echo "3" > 3
git add 3
git commit -m "3"

echo "2" > 2
git add 2
git commit -m "2"

echo "1" > 1
git add 1
git commit -m "1"

# Filling subtree ABC
git checkout ABC

echo "C" > 3
git add 3
git commit -m "C (3')"

echo "B" > 2
git add 2
git commit -m "B (2')"

echo "A" > 1
git add 1
git commit -m "A (1')"

git checkout 123
git merge ABC -m "Merge ABC (conflicts)"
echo "C" > 3
git add 3
echo "2" > 2
git add 2
echo "A\n1" > 1
git add 1
git commit -a -m "$(cat .git/MERGE_MSG)"

git checkout master
git merge 123 -m "Merge ABC123"

pwd
