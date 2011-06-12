# master
#   *           Merge ABC123
#   |\
#   | *         Merge ABC
#   | |\
#   | | *       A
#   | | *       B
#   | | *       C
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

echo "C" > C
git add C
git commit -m "C"

echo "B" > B
git add B
git commit -m "B"

echo "A" > A
git add A
git commit -m "A"

git checkout 123
git merge ABC -m "Merge ABC"

git checkout master
git merge 123 -m "Merge ABC123"

pwd
