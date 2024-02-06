# LASTools nessary
# Чтобы установить LAS Tools. Для этого:
# 1. Скачать вот отсюда https://rapidlasso.com/lastools/  zip file
# 2. Просто распаковать его в любую папку с нормальным путём.
# 3. Это путь указать в этом скрипте в парпаметрах DEM_TOOL и SHP_TOOL

import glob
import subprocess
import os
import processing



# USER_SETTING 1 -- path to las
las_folder = wrk = r'D:\Also\Genplan\2023'

# USER_SETTING 2  Set True , if shp file is need
do_shp = False

# USER_SETTING 3
resolution = 2

# USER_SETTING 3  Set True for 'relief only' filter
relief = True # False # 

# Soft Settings
DEM_TOOL = r'C:\LAStools\bin\las2dem.exe'
SHP_TOOL = r'C:\LAStools\bin\las2shp.exe'

def las2shp(las_file):
    shp_file = baseName+'_tmp.shp'
    subprocess.call([SHP_TOOL, '-i', las_file, '-o', shp_file])
    
    #if code == 0:
    #    print('Las tools is running')
    #else:
    #    print('Las tools is NOT running')
    
    temp1 = baseName+'_S_tmp.shp'
    temp2 = baseName+'_Z_2tmp.shp'
    result_shp = baseName+'_Z.gpkg'
    processing.run("native:multiparttosingleparts", {
                                                'INPUT': shp_file,
                                                'OUTPUT': temp1
                                                })
                                                
    processing.run("saga:addcoordinatestopoints", {
                                                'INPUT': temp1,
                                                'OUTPUT': temp2,
                                                'X':False,
                                                'Y':False,
                                                'Z':True,
                                                'M':False,
                                                'LON':False,
                                                'LAT':False
                                                })
                                                
    processing.run("native:fieldcalculator", {
                                            'INPUT': temp2,
                                            'FIELD_NAME':'H_ABS',
                                            'FIELD_TYPE':0,
                                            'FIELD_LENGTH':6,
                                            'FIELD_PRECISION':2,
                                            'FORMULA':' round("Z", 2)',
                                            'OUTPUT': result_shp
                                            })
                                            
        
def las2shp_dem(las_file):
    las_file = las
    baseName = las[:-4]
    dem_file = baseName+'.tif'
    
    
    print(las_file)
    if relief is True:
        code = subprocess.call([DEM_TOOL, '-i', las_file, '-o', dem_file, '-step', str(resolution),'-keep_class', '2'])
    else:
        code = subprocess.call([DEM_TOOL, '-i', las_file, '-o', dem_file, '-step', str(resolution)])
    
    if do_shp is True:
        las2shp(las_file)
        

print('Processing......')
os.chdir(wrk)
las_lst = []
for files in os.listdir(wrk):
    if files.endswith('.las'):
        las_lst.append(os.path.abspath(files))
        
for las in las_lst:
    las2shp_dem(las)
    
    
os.chdir(wrk)
for f in glob.glob("*tmp.*"):
    try:
        os.remove(f)
    except:
        pass

# Объединяем все растры в один
print('MERGING rastrs')
merged_rastr = '!_RASTR.tif'
if os.path.isfile(merged_rastr):
    print('REMOVE OLD RASTR')
    os.remove(merged_rastr)
tif_lst = [f for f in glob.glob('*.tif')]
processing.run("gdal:merge", {'INPUT': tif_lst,
                                'PCT':False,
                                'SEPARATE':False,
                                'NODATA_INPUT':None,
                                'NODATA_OUTPUT':999,'OPTIONS':'','EXTRA':'','DATA_TYPE':5,
                                'OUTPUT': merged_rastr})

print('Finished')