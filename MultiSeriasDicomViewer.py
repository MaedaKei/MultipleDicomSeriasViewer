#https://www.useful-python.com/matplotlib-layout-grid/
#https://matplotlib.org/stable/api/widgets_api.html
import argparse
from MDSV_Functions_v9 import dicom_viewer_base
from MDSV_Functions_v9 import Function_Balance_Control
from MDSV_Functions_v9 import ImageToneCorrection #CT画像の階調機能
from MDSV_Functions_v9 import ImageSlideShow #スライドショー機能
from MDSV_Functions_v9 import ImageZoom #拡大機能

#必要な引数
def dicom_viewer_arguments(args_list=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('img_folders',type=str,nargs='*',help='dcmファイルがまとめられているフォルダを入力')
    parser.add_argument('--image_type','-it',type=str,default='dcm',help='対象とする画像の拡張子を指定')
    parser.add_argument('--col_limit','-cl',type=int,default=30,help='表示したい画像の画素値幅と比較して、グレイスケールかカラー画像か変える')
    parser.add_argument('--CT_gray_range',type=int,nargs=2,default=[-180,180],help="CT画像の諧調の初期値")
    #parser.add_argument('--clip_image','-ci',nargs=2,type=float,help='画像の画素値を諧調する')
    args=parser.parse_args(args_list)
    return args
    
def dicom_viewer(args):
    need_ROWs=dicom_viewer_base.need_ROWs+ImageSlideShow.need_ROWs+ImageZoom.need_ROWs+ImageToneCorrection.need_ROWs
    #need_ROWs=dicom_viwer_base.need_ROWs+image_clip.need_ROWs
    #必要な変数を持っているので何か機能を追加するときは引数にbase_instanceを渡すようにする
    #dicom_viwer_baseの略
    base_instance=dicom_viewer_base(args,need_ROWs)
    Function_Balance_Controler=Function_Balance_Control(base_instance)
    
    imagetonecorrection=ImageToneCorrection(base_instance,Function_Balance_Controler)
    imageslideshow=ImageSlideShow(base_instance,Function_Balance_Controler)
    imagezoom=ImageZoom(base_instance,Function_Balance_Controler)
    base_instance.show()


if __name__=='__main__':
    args=dicom_viewer_arguments()
    dicom_viewer(args)
