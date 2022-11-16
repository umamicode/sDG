
# $1 gpuid
# $2 runid

# base method
#svroot=saved-digit/base_run${2}
#python3 main_base.py --gpu $1 --data mnist --epochs 50 --nbatch 100 --lr 1e-4 --svroot $svroot
#python3 main_test_digit.py --gpu $1 --modelpath $svroot/best.pkl --svpath $svroot/test.log

# AutoAugment method
#for autoaug in AA RA
#do
#    svroot=saved-digit/${autoaug}_run${2}
#    python3 main_base.py --gpu $1 --data mnist --autoaug ${autoaug} --epochs 50 --nbatch 100 --lr 1e-4 --svroot $svroot
#    python3 main_test_digit.py --gpu $1 --modelpath $svroot/best.pkl --svpath $svroot/test.log
#done

# my method
w_cls=1.0
w_cyc=20
w_info=0.1
w_div=2.0
div_thresh=0.5
w_tgt=1.0

gen=cnn
interpolation=img
backbone=custom
pretrained=False
n_tgt=20
max_tgt=19

#For ReliC: Either (--relic / --no-relic)
#tgt_epochs: How many epochs were trained on each target domain (author setting:30)

#for w_div in 0.2 0.4 0.6 0.8 1.0 1.2 1.4 1.6 1.8 
#for w_info in 0 0.1 0.2 0.5 1.0 #3.0 #0.001 0.005 0.01 0.02 0.03 0.04 0.05 0.1
#for w_cyc in 40 50 
#do

#added backbone to svroot
#svroot=saved-digit/${gen}_${interpolation}_${w_cls}_${w_cyc}_${w_info}_${w_div}_${div_thresh}_${w_tgt}_run${2}
svroot=saved-digit/${gen}_${interpolation}_${backbone}_${pretrained}_${w_cls}_${w_cyc}_${w_info}_${w_div}_${div_thresh}_${w_tgt}_run${2}
baseroot=saved-digit/base_${backbone}_${pretrained}_run0/best.pkl

# step1
python3 main_my_iter.py --gpu $1 --data mnist --gen $gen --relic --backbone ${backbone} --interpolation $interpolation --n_tgt ${n_tgt} --tgt_epochs 30 --tgt_epochs_fixg 15 --nbatch 100 --batchsize 128 --lr 1e-4 --w_cls $w_cls --w_cyc $w_cyc --w_info $w_info --w_div $w_div --div_thresh ${div_thresh} --w_tgt $w_tgt --ckpt ${baseroot} --svroot ${svroot} 
python3 main_test_digit.py --gpu $1 --modelpath ${svroot}/${max_tgt}-best.pkl --svpath ${svroot}/test.log --backbone ${backbone} 

#done

