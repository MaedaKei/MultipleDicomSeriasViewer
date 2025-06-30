import os,glob
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider,Button,RectangleSelector,SpanSelector
from matplotlib import gridspec
#https://www.useful-python.com/matplotlib-layout-grid/
#https://matplotlib.org/stable/api/widgets_api.html
import pydicom as dicom
import numpy as np
from colormap_v2 import colormap
from functools import partial

VolumeImage_list=[]
class dicom_viewer_base:
    """
    Dicom_viewerの基本の機能を実装したクラス
    画像の表示と配置を担う
    """
    need_ROWs=1#画像
    def __init__(self,args,ax_rows):
        #画像を読み込むための関数を切り替え
        if args.image_type=='dcm':
            img2ndarray=self.dicom2ndarray
        elif args.image_type=='png':
            img2ndarray=self.png2ndarray
        #各ディレクトリのdcmファイルのパスをまとめる。このとき、枚数を合わせる
        file_num_list=[]#各ディレクトリのファイル数を格納
        dcm_path_list=[]#各ディレクトリのファイルパスを格納
        self.row_counter=0#行をカウントしておく
        for dcm_folder in args.img_folders:
            if os.path.isdir(dcm_folder)!=True:
                print(f"引数にディレクトリではないものがある :{dcm_folder}")
                return
            this_dir_dcms=sorted(glob.glob(os.path.join(dcm_folder,'*.'+args.image_type)))
            dcm_path_list.append(this_dir_dcms)
            file_num_list.append(len(this_dir_dcms))
        max_file_num=max(file_num_list)
        start_dir=os.getcwd()

        self.VolumeImage_info_list=[]
        CT_id_list=[]
        max_pixel_range=1
        MASK_count=0
        CT_count=0
        for dir_num in range(len(dcm_path_list)):#ディレクトリ毎に画像を読み込んでいく
            dcm_pathes=dcm_path_list[dir_num]
            now_file_num=len(dcm_pathes)
            add_num=max_file_num-now_file_num
            end=add_num//2
            start=add_num-end
            images=[]#各ディレクトリ内の画像を読み込んで格納
            print(f"{args.img_folders[dir_num]},{now_file_num} \t:",end='')
            os.chdir(args.img_folders[dir_num])
            for load_dcm_path in sorted(dcm_pathes):
                img=img2ndarray(os.path.basename(load_dcm_path))
                images.append(img)
            images=np.array(images)#(pic_num,H,W)
            _,H,W=images.shape
            #読み込んだ3Dvolume
            images=np.concatenate([np.zeros((start,H,W)),images,np.zeros((end,H,W))])
            #セグメンテーションかどうか判断
            pixel_unique,pixel_hist=np.unique(images,return_counts=True)
            print(f"{pixel_unique[0]} ~ {pixel_unique[-1]}")
            #ヒストグラムで一番個数が多いのは多分無駄なバックグラウンドなのでここを0にする
            pixel_hist[np.argmax(pixel_hist)]=0
            #self.hist_list.append([pixel_unique,(pixel_hist+10000)**(1/3)])
            #ヒストグラム
            hist=[pixel_unique,(pixel_hist+10000)**(1/3)]
            #ユニークの最大値と最小値から予測されるユニークの種類
            pixel_range=pixel_unique[-1]-pixel_unique[0]+1
            #print(pixel_unique,pixel_range)
            IsMask=False
            if len(pixel_unique)<=pixel_range and pixel_range<=args.col_limit:
                IsMask=True
                MASK_count+=1
                max_pixel_range=max(max_pixel_range,pixel_range)
            else:
                CT_count+=1
                CT_id_list.append(dir_num)
            #self.SEG_OR_NOT.append(seg_check)
            #print(images.shape)
            if IsMask:
                color=colormap(color_num=int(max_pixel_range))
            else:
                color=("gray",None)
            #画像の実体はVolumeImage_list
            VolumeImage_list.append(images)
            #画像の情報はVolumeImage_info_listにまとめる
            #どのDICOMSeriasを表示するか、カラーマップ、透過率、画素値のヒストグラム、マスク画像か否か
            self.VolumeImage_info_list.append({"volumeimage_list":[dir_num],"colormap":[color],"alpha":[1],"hist_list":[hist],"IsMask":IsMask})
            os.chdir(start_dir)
        #init_slice=0
        """
        CT画像とマスク画像のオーバーレイの有無、差分画像の有無を決定して条件を書き換える。
        オーバーレイ表示をする条件 -> 入力されたディレクトリのDCM画像の種類がCTx1, MASKxNの場合、CTを下にしてオーバーレイ表示を実行する。
        差分画像の表示をする条件 -> MASKx2の場合
        よって、制作者的には CT MASK MASKの感じで指定してくれるとありがたい

        どの指定ディレクトリがCT,MASKかはself.SEG_OR_NOTで管理できているはず
        """
        if MASK_count==2:
            #差分画像生成
            MASK_image_list=[]
            for Volumeimage_info in self.VolumeImage_info_list:
                if Volumeimage_info["IsMask"]:
                    MASK_image_list.append(Volumeimage_info["volumeimage_list"][0])
            #new_volume_image=np.abs(VolumeImage_list[MASK_image_list[0]]-VolumeImage_list[MASK_image_list[1]])
            new_volume_image=VolumeImage_list[MASK_image_list[0]]!=VolumeImage_list[MASK_image_list[1]]
            pixel_unique,pixel_hist=np.unique(new_volume_image,return_counts=True)
            #ヒストグラムで一番個数が多いのは多分無駄なバックグラウンドなのでここを0にする
            #pixel_hist[np.argmax(pixel_hist)]=0
            #ヒストグラム
            hist=[pixel_unique,(pixel_hist+10000)**(1/3)]
            VolumeImage_list.append(new_volume_image)
            new_id=len(VolumeImage_list)-1
            self.VolumeImage_info_list.append({"volumeimage_list":[new_id],"colormap":[("Reds",None)],"alpha":[1],"hist_list":[hist],"IsMask":True})
        
        if CT_count==1 and MASK_count>0:#オーバーレイ機能ON
            CT_data=self.VolumeImage_info_list.pop(CT_id_list[0])
            for VolumeImage_info in self.VolumeImage_info_list:
                VolumeImage_info["volumeimage_list"].insert(0,CT_id_list[0])#CT_count==1よりCT_id_listも長さ1
                VolumeImage_info["colormap"].insert(0,CT_data["colormap"][0])
                VolumeImage_info["alpha"]=[1,0.4]
                VolumeImage_info["hist_list"].insert(0,CT_data["hist_list"][0])#マスクの階調は行う必要ないので、CT用のヒストグラムを入れておく
        
        volume_num=len(self.VolumeImage_info_list)
        height_ratios=np.ones(ax_rows)*0.3
        height_ratios[0]=25
        self.gs=gridspec.GridSpec(ax_rows,volume_num,height_ratios=height_ratios,hspace=0.01,wspace=0.05,top=0.99,bottom=0.01,right=0.99,left=0.01)
        #self.tone_button_list=[]
        #画像ごとに表示する
        self.fig=plt.figure(num="DicomViwer",figsize=(10,5.3))
        #print(self.all_images.shape)
        
        for volume_n in range(volume_num):
            VolumeImage_info=self.VolumeImage_info_list[volume_n]
            self.row_counter=0
            #ディレクトリ毎の画像表示
            img_ax=self.fig.add_subplot(self.gs[self.row_counter,volume_n])
            self.row_counter+=1
            img_ax.axis('off')
            VolumeImage_info["img_ax"]=img_ax
            VolumeImage_info["img_table"]=[]
            for i in range(len(VolumeImage_info["volumeimage_list"])):
                image_id=VolumeImage_info["volumeimage_list"][i]
                cmap,norm=VolumeImage_info["colormap"][i]
                alpha=VolumeImage_info["alpha"][i]
                #ヒストグラムｘ軸の最小値と最大値
                vmin=VolumeImage_info["hist_list"][i][0][0]
                vmax=VolumeImage_info["hist_list"][i][0][-1]
                #画像の一枚目でnorm.vmin,norm.vmaxが決定されてしまうため、手動で設定する
                img_table=img_ax.imshow(VolumeImage_list[image_id][0],cmap=cmap,norm=norm,alpha=alpha)
                #print(vmin,vmax)
                img_table.norm.vmin=vmin
                img_table.norm.vmax=vmax
                VolumeImage_info["img_table"].append(img_table)
            if not (VolumeImage_info["IsMask"]==True and len(VolumeImage_info["img_table"])==1):
                VolumeImage_info["img_table"][0].norm.vmin=min(args.CT_gray_range)
                VolumeImage_info["img_table"][0].norm.vmax=max(args.CT_gray_range)
            
    def dicom2ndarray(self,dicom_file):
        ref=dicom.dcmread(dicom_file,force=True)
        img=ref.pixel_array
        return img
    def show(self):
        plt.show()

"""
各種機能を追加する↓
引数 : base_instance
dicom_viewer_baseクラスをインスタンス化したもの。必要な情報をインスタンス変数として保持してあるので、各種機能の実装で必要なものを参照する。
"""
# 各機能でボタンやマウス操作を割り当てると同じ操作に複数の機能が割り当てられることがあるため、
# 状態を監視して各機能をON/OFFするクラス
class Function_Balance_Control:
    """
    2025/06/08
    画像のlogal/globalスライス : マウスの位置でlocal, globalを切り替えてマウスホイールでスライドショー
    """
    def __init__(self,base_instance):
        self.fig=base_instance.fig
        self.VolumeImage_info_list=base_instance.VolumeImage_info_list
        #マウスの位置を監視
        #画像内にマウスがあるか、ないか
        self.ax_selected=False
        self.selected_ax=None
        self.selected_ax_number=None
        self.fig.canvas.mpl_connect("axes_enter_event",self.axes_enter_event)
        self.fig.canvas.mpl_connect("axes_leave_event",self.axes_leave_event)
        #ボタンの押下の可否を監視
        #ボタンは複数押されるかもしれないので空リストをデフォルトとする
        #まずは普通の変数として、複数押下時の反応を見てみる
        self.pressed=False
        self.pressed_button=None
        self.fig.canvas.mpl_connect("key_press_event",self.key_press_event)
        self.fig.canvas.mpl_connect("key_release_event",self.key_release_event)
        #各機能のON/OFFフラグの初期値
        self.ImageToneCorrection_FLAG=False
        self.ImageSlideShow_FLAG=True
        self.ImageZoom_FLAG=False

    """
    マウスやキーの状態を監視する基本的な関数群
    基本的に、最後に各機能のフラグ更新を行う
    """
    def axes_enter_event(self,event):
        self.ax_selected=True
        self.selected_ax=event.inaxes
        for i,VolumeImage_info in enumerate(self.VolumeImage_info_list):
            if self.selected_ax==VolumeImage_info["img_ax"]:
                self.selected_ax_number=i
                break
        self.function_balance_control()

    def axes_leave_event(self,event):
        self.ax_selected=False
        self.selected_ax_number=None
        self.function_balance_control()

    def key_press_event(self,event):
        self.pressed=True
        self.pressed_button=event.key
        self.function_balance_control()

    def key_release_event(self,event):
        self.pressed=False
        self.pressed_button=None
        self.function_balance_control()
    """
    基本的な関数群によって変化するフラグを見て、対象の関数の機能がONとなるかOFFとなるか判断する関数
    """
    def function_balance_control(self):
        #諧調補正の起動
        #画像内で右クリックをする
        #画像内右クリックがほかの機能にも割り当てられれば、新しく条件を追加する必要がある
        self.ImageToneCorrection_FLAG=(True if self.ax_selected==True else False)
        #マウスがグラフ内にあり、Ctrlボタンが押されているならimage_sliceはOFF
        #そのうち、ボタンが押されているならOFFという条件に難化するかも
        #このフラグはスライドショーに適用され、spaceボタンによる位置合わせには適用されない
        self.ImageSlideShow_FLAG=(False if self.ax_selected==True and self.pressed_button=="control" else True)
        #マウスがグラフ内にあり、Ctrlボタンが押されているならimage_sliceはON
        self.ImageZoom_FLAG=(True if self.ax_selected==True and self.pressed_button=="control" else False)

class ImageToneCorrection:
    need_ROWs=0
    def __init__(self,base_instance,Function_Balance_Controler):
        self.VolumeImage_info_list=base_instance.VolumeImage_info_list
        self.fig=base_instance.fig
        self.Function_Balance_Controler=Function_Balance_Controler
        self.fig.canvas.mpl_connect("button_press_event",self.ToneCorrection_activate_event)
        
        print(f"{self.__class__.__name__} Registerd !")
    
    def ToneCorrection_activate_event(self,event):
        if self.Function_Balance_Controler.ImageToneCorrection_FLAG and event.button==3:
            volume_id=self.Function_Balance_Controler.selected_ax_number
            hist=self.VolumeImage_info_list[volume_id]["hist_list"][0]
            self.image_table=self.VolumeImage_info_list[volume_id]["img_table"][0]#オーバーレイされていればCTを対象とする
            self.tone_window_fig=plt.figure(num=self.__class__.__name__,figsize=(5,4),tight_layout=True,clear=True)
            self.tone_window_gs=gridspec.GridSpec(3,1,height_ratios=[20,0.5,0.5])
            hist_ax=self.tone_window_fig.add_subplot(self.tone_window_gs[0,0])
            self.center_slice_ax=self.tone_window_fig.add_subplot(self.tone_window_gs[1,0],sharex=hist_ax)
            self.range_slice_ax=self.tone_window_fig.add_subplot(self.tone_window_gs[2,0])
            hist_ax.plot(*hist,color='#000000')
            hist_ax.tick_params(labelleft=False)
            #現在の画素値範囲,元の画素値範囲
            now_lower,now_upper=self.image_table.norm.vmin,self.image_table.norm.vmax
            original_lower,original_upper=hist[0][0],hist[0][-1]
            #スライダーを動かして更新されるやつらは変数に入れておく
            self.value_text=hist_ax.set_title(f"[ {now_lower} ~ {now_upper} ]")
            self.lower_limit_line=hist_ax.axvline(now_lower,color="#FF0000",alpha=0.5)
            self.upper_limit_line=hist_ax.axvline(now_upper,color="#FF0000",alpha=0.5)
            self.center_slice=Slider(ax=self.center_slice_ax,label='center',valmin=original_lower,valmax=original_upper,
                                valinit=(now_lower+now_upper)/2,valstep=1,valfmt='%d',handle_style={'size':5})
            self.range_slice=Slider(ax=self.range_slice_ax,label='range',valmin=0,valmax=original_upper-original_lower,
                                valinit=now_upper-now_lower,valstep=1,valfmt='%d',handle_style={'size':5})
            self.center_slice.on_changed(self.slice_moved)
            self.range_slice.on_changed(self.slice_moved)
            plt.show()
    def slice_moved(self,val):
        half_range=self.range_slice.val/2
        min=self.center_slice.val-half_range
        max=self.center_slice.val+half_range
        self.image_table.norm.vmin=min
        self.image_table.norm.vmax=max
        self.value_text.set_text(f"[ {min} ~ {max} ]")
        self.lower_limit_line.set_xdata([min,min])
        self.upper_limit_line.set_xdata([max,max])
        self.tone_window_fig.canvas.draw_idle()
        self.fig.canvas.draw_idle()

class ImageSlideShow:
    """
    画像のスライドショー機能を実装したクラス
    localスライダー、globalスライダーを持つ。
    localスライダーはスライドボタン＆マウスホイール、globalスライダーはマウスホイールのみ
    Alignment：
    すべての表示位置を合わせる機能。
    ある画像にそろえる機能LAlignmentとすべて最初の画像にそろえるGAlignmentを持つ
    Alignmentの操作はマウスの位置とspaceキーで制御する
    """
    #local slicer
    #global slicer →　マウスホイールに割り当て
    #slice RESET button　→　マウスによる画像選択+spaceボタンに割り当て
    need_ROWs=1
    def __init__(self,base_instance,Function_Balance_Controler):
        self.VolumeImage_info_list=base_instance.VolumeImage_info_list
        self.fig=base_instance.fig
        self.Function_Balance_Controler=Function_Balance_Controler
        self.slicer_length=len(VolumeImage_list[0])
        
        volume_num=len(self.VolumeImage_info_list)
        self.each_slicer_list=[]
        for volume_n in range(volume_num):
            ax=base_instance.fig.add_subplot(base_instance.gs[base_instance.row_counter,volume_n])
            slicer=Slider(
                ax=ax,label=None,valinit=0,valmin=0,valmax=self.slicer_length-1,
                valfmt='%d',valstep=1,orientation='horizontal',
                handle_style={'size':5}
            )
            slicer.on_changed(partial(
                self.each_slicer_changed,volume_n=volume_n
            ))
            #self.each_slicer_list.append(slicer)
            self.VolumeImage_info_list[volume_n]["slicer"]=slicer
        base_instance.row_counter+=1

        self.fig.canvas.mpl_connect("scroll_event",self.slicer_scroll_event)

        self.fig.canvas.mpl_connect("key_press_event",self.SliceReset_space_pressed_event)
        print(f"{self.__class__.__name__} Registerd !")
    
    def each_slicer_changed(self,dammy_args,volume_n):
        image_table_list=self.VolumeImage_info_list[volume_n]["img_table"]
        index=self.VolumeImage_info_list[volume_n]["slicer"].val
        image_id_list=self.VolumeImage_info_list[volume_n]["volumeimage_list"]
        for image_table,image_id in zip(image_table_list,image_id_list):
            image_table.set_data(VolumeImage_list[image_id][index])
        self.fig.canvas.draw_idle()
    
    def slicer_scroll_event(self,event):
        if self.Function_Balance_Controler.ImageSlideShow_FLAG:
            if event.button=="up":
                change_value=-1
            elif event.button=="down":
                change_value=1
            if self.Function_Balance_Controler.ax_selected:
                #画像内にマウスがあるなら
                # local slice mode
                slicer=self.VolumeImage_info_list[self.Function_Balance_Controler.selected_ax_number]["slicer"]
                slicer.set_val((slicer.val+change_value)%self.slicer_length)
            else:
                #画像内にマウスがないなら
                # global slice mode
                for VolumeImage_info in self.VolumeImage_info_list:
                    slicer=VolumeImage_info["slicer"]
                    slicer.set_val((slicer.val+change_value)%self.slicer_length)
            self.fig.canvas.draw_idle()
    def SliceReset_space_pressed_event(self,event):
        if event.key==" ":
            if self.Function_Balance_Controler.ax_selected:
                #マウスがさしている画像の位置を取得
                index=self.VolumeImage_info_list[self.Function_Balance_Controler.selected_ax_number]["slicer"].val
            else:
                #マウスがどこもさしていないので０に合わせる
                index=0
            
            for VolumeImage_info in self.VolumeImage_info_list:
                VolumeImage_info["slicer"].set_val(index)
            self.fig.canvas.draw_idle()

class ImageZoom:
    """
    画像の拡大機能を実装したクラス。画像の縮小はできないのでリセットボタンで元に戻す。

    画像を並べている状態でどれかの画像を拡大すると、並べてある画像すべてで同じように拡大できる。
    """
    need_ROWs=1#clip_reset_button
    def __init__(self,base_instance,Function_Balance_Controler):
        self.fig=base_instance.fig
        self.VolumeImage_info_list=base_instance.VolumeImage_info_list
        self.Function_Balance_Controler=Function_Balance_Controler

        #self.img_ax_list=base_instance.img_ax_list
        #self.clips=[]
        for VolumeImage_info in self.VolumeImage_info_list:
            img_ax=VolumeImage_info["img_ax"]
            VolumeImage_info["zoom"]=RectangleSelector(
                img_ax,self.clip_callback,useblit=True,
                #これ以下のピクセル範囲だったらアクティブにならないってこと
                minspanx=5,minspany=5,spancoords='pixels',interactive=False,
                props=dict(edgecolor='#FF0000',alpha=1,fill=False)
            )
        clip_reset_ax=self.fig.add_subplot(base_instance.gs[base_instance.row_counter,:])
        self.clip_reset_button=Button(clip_reset_ax,label='ZOOM RESET',color='#0000b0',hovercolor='#0000f0')
        self.clip_reset_button.on_clicked(self.push_clip_reset)
        self.original_H,self.original_W=VolumeImage_list[0][0].shape#H,W
        print(f"{self.__class__.__name__} Registerd !")
        
    def clip_callback(self,eclick,erelease):
        w1,h1=int(eclick.xdata),int(eclick.ydata)
        w2,h2=int(erelease.xdata),int(erelease.ydata)
        if h1<h2 and w1<w2:
            for VolumeImage_info in self.VolumeImage_info_list:
                ax=VolumeImage_info["img_ax"]
                ax.set_xlim(w1,w2)
                ax.set_ylim(h2,h1)
            self.fig.canvas.draw_idle()
    def push_clip_reset(self,dammy):
        for VolumeImage_info in self.VolumeImage_info_list:
            ax=VolumeImage_info["img_ax"]
            ax.set_xlim(0,self.original_W)
            ax.set_ylim(self.original_H,0)
        self.fig.canvas.draw_idle()