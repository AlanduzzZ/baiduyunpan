# 百度云盘群分享文件搜索
列出百度云群分享中的文件夹列表，方便搜索

## 用法

1、找出BDUSS、STOKEN

登录百度云主页：https://pan.baidu.com
F12打开调试控制台，切换到Application标签，在左侧Storage菜单中选中Cookies子菜单，选择https://pan.baidu.com 条目。在右侧找到BDUSS_BFESS(对应BDUSS)和STOKEN值。
![image](https://user-images.githubusercontent.com/10544715/147460998-b84db524-f1ac-472e-8dbb-121a3b37bdd9.png)



2、找出BAIDU_STATIC_PARAMETER定义的固定值

F12打开调试控制台，打开群文件库，在Network标签下找到listshare开头的Url，在右侧Headers中可找到相应固定值
![image](https://user-images.githubusercontent.com/10544715/147461138-d84ffbab-0fd6-4663-bb7d-7d76ddc34833.png)

3、将如上值填入脚本对应变量中，运行脚本即可

## 注意
默认每次翻页只取第一页，且最大200个条目
