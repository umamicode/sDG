
# $1 gpuid
# $2 runid

# base method
data=mnist
backbone=resnet18
svroot=saved-digit/base_${backbone}_run${2}
#baseroot= saved-digit/base_run0_${backbone}/best.pkl

python3 main_base.py --gpu $1 --data ${data} --epochs 50 --nbatch 100 --lr 1e-4 --svroot $svroot --backbone ${backbone}
python3 main_test_digit.py --gpu $1 --modelpath $svroot/best.pkl --svpath $svroot/test.log --backbone ${backbone} 


