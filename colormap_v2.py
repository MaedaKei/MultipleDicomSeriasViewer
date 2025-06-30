import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import colorsys
import argparse

def colormaps_arguments(arg_list=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--color_num','-cn',type=int,default=24,help='何色ほしいか')
    parser.add_argument('--mode',type=int,default=0)
    args=parser.parse_args(arg_list)
    return args

def colormap(color_num=30,mode=0):
    cmap='gray'
    norm=None
    N=color_num
    #色相を一周させる
    HSV_tuples=[(n/N,1,1) for n in range(N-1)]#黒の分を抜く
    RGB_tuples=np.array([colorsys.hsv_to_rgb(*hsv) for hsv in HSV_tuples])
    RGB_tuples=np.insert(RGB_tuples,0,[0,0,0],axis=0)
    RGB_list=[]
    #透過度を追加する
    alpha=np.ones(len(RGB_tuples))
    alpha[0]=0#黒色の透過度を0にする
    alpha=alpha.reshape(-1,1)
    RGB_list.append(np.concatenate([RGB_tuples,alpha],axis=1))
    RGB_tuples=255*RGB_tuples
    RGB_list.append([f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}" for rgb in RGB_tuples.astype(np.int64)])
    #print(N,len(RGB_tuples))
    rgb=RGB_list[mode]
    #print(rgb)
    cmap=colors.ListedColormap(rgb)
    #print(cmap.N)
    norm=colors.BoundaryNorm(np.arange(cmap.N+1)-0.5,cmap.N)#映したい画素値がビンの境界に設定されると変な感じになるので0の色になるが措置の範囲は-0.5～0.5、1は0.5～1.5という風にした
    """
    print(norm.N)
    print(norm.boundaries)
    for i in norm.boundaries:
        print(i,norm(i))
    """
    return cmap,norm
    #画像化
if __name__=='__main__':
    color_num=21
    try:
        npz=np.load('img_file.npz')
        key=npz.files
        x=npz[key[0]]
        x=x[150:300,180:330]#(H,W)
    except Exception as e:
        print(e)
        x=np.arange(color_num)
        x=np.tile(x,(len(x),1))
    color_unique=np.unique(x)
    print(color_unique)
    #color_num=color_unique[-1]
    args_text=f"-cn {color_num} --mode 0"
    color_args=colormaps_arguments(args_text.split())
    cmap,norm=colormap(color_args.color_num,color_args.mode)
    cn=color_args.color_num
    for color in color_unique:
        print(norm(color))
    plt.imshow(x,cmap=cmap,norm=norm)
    plt.xticks(np.arange(color_num))
    plt.show()