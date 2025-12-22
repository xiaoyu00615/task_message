[app]

# 1. 应用基本信息（保留你的配置）
title = 任务管理          
package.name = taskmessage   
package.domain = org.test    
version = 0.1                

# 2. 项目文件配置（保留你的配置，补充中文路径兼容）
source.dir = .               
source.include_exts = py,kv,png,jpg,ttf,atlas  
source.exclude_exts = pyc,pyo,log,git          
source.exclude_dirs = venv,.git,__pycache__    
# 新增：强制UTF-8编码，避免中文文件名乱码
android.charset = utf-8

# 3. 依赖配置（优化国内安装）
requirements = python3,kivy==2.3.0,pillow
# 新增：指定pip国内源（Buildozer打包时安装Python依赖用）
android.pip_index_url = https://pypi.tuna.tsinghua.edu.cn/simple
android.pip_trusted_host = pypi.tuna.tsinghua.edu.cn

# 4. Android核心配置（全量替换国内镜像，关键！）
android.api = 33             
android.ndk = 25b            
android.minapi = 24
# 新增：SDK/NDK/ANT/Gradle国内镜像下载地址（清华源）
android.sdk_url = https://mirrors.tuna.tsinghua.edu.cn/android/repository/commandlinetools-linux-10406996_latest.zip
android.ndk_url = https://mirrors.tuna.tsinghua.edu.cn/android/repository/android-ndk-r25b-linux.zip
android.ant_url = https://mirrors.tuna.tsinghua.edu.cn/apache/ant/binaries/apache-ant-1.10.14-bin.tar.gz
android.gradle_url = https://mirrors.tuna.tsinghua.edu.cn/gradle/gradle-7.5-bin.zip
# 新增：SDK仓库镜像（替代谷歌官方仓库）
android.sdk_repository = https://mirrors.tuna.tsinghua.edu.cn/android/repository/
# 留空自动使用镜像路径，无需手动填
android.ndk_path =           
android.sdk_path =           

# 5. Android权限（保留你的配置，补充常用权限）
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_WIFI_STATE

# 6. 资源配置（保留你的配置，补充路径兼容）
android.icon = icons/icon.png       
android.presplash = icons/splash.png 
android.add_android_assets = assets/ 
# 修正Cython路径（适配Ubuntu 20.04默认路径，避免找不到）
android.cython = /usr/local/bin/cython

# 7. 界面配置（保留你的配置）
orientation = portrait       
fullscreen = 0               
android.add_activiti_flags = android:windowSoftInputMode=adjustResize
android.bootstrap = sdl2

# 8. 新增：禁用谷歌服务检查（避免访问谷歌失败）
android.google_play_store = False
android.enable_androidx = True  
# 兼容新版AndroidX库

[buildozer]
# 日志级别（保留）
log_level = 2                
warn_on_root = 1             
# 新增：Buildozer缓存目录（可选，指定到D盘避免C盘满）
# build_dir = /mnt/d/Idea/Trae/app/tasks_message/.buildozer
# 新增：强制使用国内镜像下载所有依赖
disable_remote_build = True