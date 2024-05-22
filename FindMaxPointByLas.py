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
wrk = r'D:\TOOLS\FindMaxPoint\wrk'

# USER_SETTING 2 -- areas_path_file
areas = r'D:\TOOLS\FindMaxPoint\wrk\areas.gpkg'

# CONSTANT path
# USER_SETTING 3 -- relief rastr
relief_rastr = r'D:\Also\Genplan\_rastrs\!_Type1A_2023.tif'

# USER_SETTING 4 -- path to las
las_folder = r'D:\TOOLS\FindMaxPoint\data_las'

# USER_SETTING 5 -- номенклатура планшетов
planshet_nom = r'D:\wrk_TORIS\package_160\src\all_twn\PL2000_polygon_fxd.gpkg'

# Soft Settings
SHP_TOOL = r'C:\LAStools\bin\las2shp.exe'

user_crs = 'USER:100020'
def las2shp(las_file):
    os.chdir(r'D:\TOOLS\FindMaxPoint\wrk')
    baseName = (os.path.basename(las_file))[:-4]
    shp_file = wrk+'\\'+baseName+'_tmp.shp'
    print(shp_file)
    subprocess.call([SHP_TOOL, '-i', las_file, '-o', shp_file])
    processing.run("qgis:definecurrentprojection", 
                    {'INPUT':shp_file,
                    'CRS':QgsCoordinateReferenceSystem(user_crs)
                    }) 
    
    result_shp = baseName+'_Z.gpkg'
    
    temp1 = processing.run("native:multiparttosingleparts", {
                                                'INPUT': shp_file,
                                                'OUTPUT': 'TEMPORARY_OUTPUT'
                                                })
                                                
    temp2 = processing.run("saga:addcoordinatestopoints", {
                                                'INPUT': temp1['OUTPUT'],
                                                'OUTPUT':'TEMPORARY_OUTPUT',
                                                'X':False,
                                                'Y':False,
                                                'Z':True,
                                                'M':False,
                                                'LON':False,
                                                'LAT':False
                                                })
                                                
    processing.run("native:fieldcalculator", {
                                            'INPUT': temp2['OUTPUT'],
                                            'FIELD_NAME':'H_ABS',
                                            'FIELD_TYPE':0,
                                            'FIELD_LENGTH':6,
                                            'FIELD_PRECISION':2,
                                            'FORMULA':' round("Z", 2)',
                                            'OUTPUT': result_shp
                                            })

    processing.run("qgis:definecurrentprojection", 
                    {'INPUT':result_shp,
                    'CRS':QgsCoordinateReferenceSystem(user_crs)
                    }) 
    return result_shp
    '''
    os.remove(shp_file)
    os.remove(shp_file[:-4]+'.shx')
    os.remove(shp_file[:-4]+'.dbf')
    '''
    

print('Processing......')
os.chdir(wrk)


# Ищем нужные планшеты
if os.path.isfile('w_p2000.gpkg'):
    os.remove('w_p2000.gpkg')
    
nom = processing.run("native:extractbylocation", 
                {
                'INPUT':planshet_nom,
                'PREDICATE':[0],
                'INTERSECT':areas,
                'OUTPUT':'w_p2000'
                })
pl_2000 = iface.addVectorLayer(nom['OUTPUT'], 'pl2000', "ogr")
features = pl_2000.getFeatures()

planshet_lst = []
for feature in features:
    pl = feature.attributes()[1]
    planshet_lst.append(pl.replace('-', '_')+'.las')
print(planshet_lst)

'''
# Находим все las в папке
las_lst = []
for files in os.listdir(wrk):
    if files.endswith('.las'):
        las_lst.append(os.path.abspath(files))
'''
merge_cloud = []
# Делаем из всех shp
for las in planshet_lst:
    las = las_folder+'\\'+las
    print(las)
    las_shp_fc = las2shp(las)
    merge_cloud.append(las_shp_fc)
    
# Объединяем все планшеты  в один
processing.run("native:mergevectorlayers", 
                {
                'LAYERS': merge_cloud,
                'CRS':QgsCoordinateReferenceSystem('USER:100020'),
                'OUTPUT':'Z_cloud.gpkg'
                })    

# Если в папке были шейпы, то удаляем
delete_files_lst=[]
for files in os.listdir(wrk):
    if files.endswith('.shp') or files.endswith('.shx') or files.endswith('.dbf') :
        delete_files_lst.append(os.path.abspath(files))
        
for f in delete_files_lst:
    try:
        os.remove(f)
    except:
        pass
    
    
# Убираем все точки вне полигонов
all_points = processing.run("gdal:clipvectorbypolygon", 
            {
            #'INPUT':'D:/TOOLS/FindMaxPoint/data_las/1628_03_Z.gpkg|layername=1628_03_Z',
            'INPUT':'Z_cloud.gpkg',
            'MASK':areas,
            'OPTIONS':'',
            'OUTPUT':'w_all_las_points.gpkg'
            })
            
            
# Читаем каждый полигон
#layer = QgsVectorLayer('areas', 'AREAS', 'ogr')
layer = iface.addVectorLayer(areas, 'areas', "ogr")

result_areas_lst = []

features = layer.getFeatures()

for feature in features:
    atr1 = feature.attributes()[0]
    print(atr1)
    # Выбираем один полигон
    processing.run("qgis:selectbyattribute", 
        {
        'INPUT':'areas',
        'FIELD':'NUM',
        'OPERATOR':0,
        'VALUE':atr1,
        'METHOD':0
        })
    
    # По маске одного полигона отбираем точки из облака. Сохраняем в файл, чтоб пользователь мог проверить
    points = processing.run("gdal:clipvectorbypolygon", 
                    {
                    #'INPUT':'D:\TOOLS\FindMaxPoint\wrk\las_points.gpkg',
                    'INPUT':all_points['OUTPUT'],
                    'MASK':QgsProcessingFeatureSourceDefinition(
                                                        'areas', 
                                                        selectedFeaturesOnly=True, 
                                                        featureLimit=-1, 
                                                        geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid
                                                        ),
                    'OPTIONS':'',
                    'OUTPUT':'w_points_'+str(atr1)+'.gpkg'
                    })        
    # Находим максимальное значение
    statistica = processing.run("qgis:basicstatisticsforfields", 
                {
                'INPUT_LAYER':points['OUTPUT'],
                'FIELD_NAME':'H_ABS'
                })
    max_value = statistica.get('MAX')
    
    # Выбираем одну точку по значению
    max_point_fc = processing.run("native:extractbyattribute", 
                {
                'INPUT':points['OUTPUT'],
                'FIELD':'H_ABS',
                'OPERATOR':0,
                'VALUE':max_value,
                'OUTPUT':'TEMPORARY_OUTPUT'
                })
    
    # Находим высоту рельефа под точкой
    relief_value_fc = processing.run("native:rastersampling", 
                    {
                    'INPUT':max_point_fc['OUTPUT'],
                    'RASTERCOPY':relief_rastr,
                    'COLUMN_PREFIX':'RELIEF_H',
                    'OUTPUT':'TEMPORARY_OUTPUT'
                    })
    
    # Находим относительную высоту точки. Сохраняем точку
    result_point = processing.run("native:fieldcalculator", {
                    'INPUT':relief_value_fc['OUTPUT'],
                    'FIELD_NAME':'H_OTN',
                    'FIELD_TYPE':0,
                    'FIELD_LENGTH':0,
                    'FIELD_PRECISION':0,
                    'FORMULA':'round("H_ABS" - "RELIEF_H1", 2)',
                    'OUTPUT':'p_MAX_a'+str(atr1)+'_'+str(max_value)+'.gpkg'
                    })
                    
    statistica = processing.run("qgis:basicstatisticsforfields", 
                {
                'INPUT_LAYER':result_point['OUTPUT'],
                'FIELD_NAME':'H_OTN'
                })
    otn_h_value = round(statistica.get('MAX'), 2)
    
    
    
    
    # Добавляем значения в атрибуты полигона
    res1 = processing.run("native:fieldcalculator", {
                        'INPUT':QgsProcessingFeatureSourceDefinition(
                                        'areas', 
                                        selectedFeaturesOnly=True, 
                                        featureLimit=-1, 
                                        geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
                        'FIELD_NAME':'H_OTN',
                        'FIELD_TYPE':0,
                        'FIELD_LENGTH':0,
                        'FIELD_PRECISION':0,
                        'FORMULA':otn_h_value,
                        'OUTPUT':'TEMPORARY_OUTPUT'})
                        
    areas_updated = processing.run("native:fieldcalculator", {
                        'INPUT':res1['OUTPUT'],
                        'FIELD_NAME':'H_ABS',
                        'FIELD_TYPE':0,
                        'FIELD_LENGTH':0,
                        'FIELD_PRECISION':0,
                        'FORMULA':max_value,
                        'OUTPUT':'w_area_result'+str(atr1)+'.gpkg'})

    #result_areas_lst.append(areas_updated['OUTPUT'])
    result_areas_lst.append(os.path.abspath('w_area_result'+str(atr1)+'.gpkg'))
    
# Объединяем все полигоны с арибутами в один
processing.run("native:mergevectorlayers", 
                {
                'LAYERS': result_areas_lst,
                'CRS':QgsCoordinateReferenceSystem('USER:100020'),
                'OUTPUT':'area_result.gpkg'
                })


# Удаляем врменные файлы     
for file in result_areas_lst:
    try:
        os.remove(file)
    except:
        pass
print('Finished')