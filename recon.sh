
# $1 gpuid
# $2 runid

# cifar10 method
w_cls=1.0
w_cyc=20
w_info=0.1 
w_oracle=1.0
w_div=2.0 #2.0
div_thresh=0.5
w_tgt=1.0
n_tgt=20
max_tgt=19
tgt_epochs=30
#lambda for ADV-BarlowTwins
lmda=0.051 #0.051 best

gen=cnn
interpolation=img
oracle=False 


data=cifar10 #mnist/cifar10/pacs
backbone=resnet18 #(custom/resnet18/resnet50/wideresnet) #mnist: custom/resnet #cifar10/pacs: resnet
pretrained=False #Only to load right base model. my_iter process is set as pretrained=False.
projection_dim=128 #default: (mnist: 128/ cifar-10:)
loss_fn=barlowtwins #supcon/barlowtwins/barlowquads/prism/vicreg
batchsize=128 

lr=1e-4
# Model Load/Save Path (baseroot softmax)
svroot=saved-model/reconquista/${data}/${gen}_${interpolation}_${backbone}_${loss_fn}_${pretrained}_${projection_dim}_${w_cls}_${w_cyc}_${w_info}_${w_div}_${div_thresh}_${w_tgt}_lmda${lmda}_oracle${oracle}_${w_oracle}_run${2}
baseroot=saved-model/newbase/${data}/base_${backbone}_${pretrained}_${projection_dim}_run0/best.pkl

# step1
python3 main_my_iter.py --gpu $1 --data ${data} --gen $gen --backbone ${backbone} --loss_fn ${loss_fn} --projection_dim ${projection_dim} --interpolation $interpolation --n_tgt ${n_tgt} --tgt_epochs ${tgt_epochs} --tgt_epochs_fixg 15 --nbatch 100 --batchsize ${batchsize} --lr $lr --w_cls $w_cls --w_cyc $w_cyc --w_info $w_info --w_div $w_div --w_oracle $w_oracle --div_thresh ${div_thresh} --w_tgt $w_tgt --ckpt ${baseroot} --svroot ${svroot} --pretrained ${pretrained} --oracle ${oracle} --lmda ${lmda}
python3 main_test.py --gpu $1 --modelpath ${svroot}/${max_tgt}-best.pkl --svpath ${svroot}/test.log --backbone ${backbone} --projection_dim ${projection_dim} --data ${data}

#done
