# Конструктор растров
# Преполагается, что ограничивающие веторные данные
# загружены в проект.
# Поле в котором указаны ограничивающие высоты ELEV_ABS
import os
import processing

# USER_SETTING_1 Folder for result files
os.chdir(r'D:\Also\Genplan\Vector')

# USER_SETTING_2  Path for relief rastr
relief_raster_path = r'D:\Also\Genplan\_rastrs\!_Type1A_2023.tif'

# USER_SETTING_3  Coord System
crs = 'USER:100020'

# USER_SETTING_4 Set True, if Type* raster is necessary and check
make_type_rastrs = False # True 

# USER_SETTING_5 Path for rastr with LEAFS (2019)
leaf_rastr = r'D:\Also\Genplan\_rastrs\!_Type1B_2019.tif'

# USER_SETTING_6 Path for vector contour LEAFS
const_leaf = r'D:\Also\Genplan\Vector\GREEN_CONSTANTA_v5.gpkg'
tempo_leaf = r'D:\Also\Genplan\Vector\GREEN_TEMPORARY_v5.gpkg'

# USER_SETTING_7
base_rastr = r'D:\Also\Genplan\_rastrs\!_Type1B_2023.tif'

# USER_SETTING_8  Исторические доминанты. (Переделать, что бралось из проекта, не из пути)
history = r'D:\Also\Genplan\Vector\HIS_PATCH_region_rastr.tif'

kind_rastr_types = {
                    #'Type_1A', Получается напрямую из las c указанием class 2. Инструмент las2dem_shp
                    #'Type_1B', Получается напрямую из las. Инструмент las2dem_shp
                    #'Type_1C', Если съёмка не 2019 года, то по сути она и есть без какой-либо зелени. Равна Type_1B
                    'Type_2A',  #  в Type_1B заталкиваем зелень 2019 года
                    'Type_2B',  #  в Type_1B заталкиваем только постоянную зелень 2019 года
                    'Type_2C',  #  одинаковый с 'Type_1C'
                    'Type_3A',
                    'Type_3B',
                    'Type_3C',
                    'Type_4A',
                    'Type_4B',
                    }


def rastr_from_elev_field(name):
    print('ELEV_ABS param')
    
    fix_geom = processing.run("native:fixgeometries", 
                    {
                    'INPUT':name, 
                    'METHOD':1,
                    'OUTPUT':'TEMPORARY_OUTPUT'
                    })
                    
    temp_value_rastr1 = processing.run("gdal:rasterize", 
                    {
                    'INPUT':fix_geom['OUTPUT'],
                    'FIELD':'ELEV_ABS',
                    'BURN':0,
                    'USE_Z':False,
                    'UNITS':1,
                    'WIDTH':2,
                    'HEIGHT':2,
                    'EXTENT':None,
                    'NODATA':0,
                    #'NODATA':999,
                    'OPTIONS':'',
                    'DATA_TYPE':5,
                    'INIT':None,'INVERT':False,'EXTRA':'',
                    'OUTPUT':'TEMPORARY_OUTPUT'})
    
    res1 = processing.run("native:fillnodata", 
                    {
                    'INPUT':temp_value_rastr1['OUTPUT'],
                    'BAND':1,
                    #'FILL_VALUE':0,
                    'FILL_VALUE':999,
                    'OUTPUT':name.name()+'_rastr.tif'
                    }
                    )

    iface.addRasterLayer(res1['OUTPUT'], str(name.name()+'_rastr'))


def remove_temp_lyr(fc):
    datas_lst = QgsProject.instance().mapLayers().values()
    
    for layer in QgsProject.instance().mapLayers().values():
        if str(layer.name()) == str(fc):
            QgsProject.instance().removeMapLayers([layer.id()])  

    
def rastr_from_rastr_values(name, extent, values_src_rastr, postfix):
    print('BUILD relief values')
    print(name.name())
    temp_value_rastr1 = processing.run("gdal:rasterize", 
                {
                'INPUT':name,
                'FIELD':'',
                'BURN':555,
                'USE_Z':False,
                'UNITS':1,
                'WIDTH':2,
                'HEIGHT':2,
                'EXTENT':extent,
                'NODATA':0,
                'OPTIONS':'',
                'DATA_TYPE':5,
                'INIT':None,
                'INVERT':False,
                'EXTRA':'',
                'OUTPUT':'TEMPORARY_OUTPUT'
                }
                )

    iface.addRasterLayer(temp_value_rastr1['OUTPUT'], 'temp_rastr_555')
    iface.addRasterLayer(relief_raster_path, 'h_val_rastr')
    
    processing.run("gdal:assignprojection", 
            {
            'INPUT':'temp_rastr_555',
            'CRS':QgsCoordinateReferenceSystem(crs)
            })
    
    output_rast = processing.run("qgis:rastercalculator", 
                    {
                    'EXPRESSION':'if("temp_rastr_555@1"=555, "h_val_rastr@1", 999)',
                    'LAYERS':[relief_raster_path],
                    'CELLSIZE':2,
                    'EXTENT':extent,
                    'CRS':QgsCoordinateReferenceSystem(crs),
                    'OUTPUT':name.name()+str(postfix)+'.tif'
                    })
    result_lyr_name = name.name()+str(postfix)
    iface.addRasterLayer(output_rast['OUTPUT'], result_lyr_name)
    remove_temp_lyr('temp_rastr_555')
    remove_temp_lyr('h_val_rastr')
    
    return result_lyr_name


def read_extent_from_file(file):
    layer = QgsVectorLayer(file)
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    return xmin, xmax, ymin, ymax


lyrs = [layer for layer in QgsProject.instance().mapLayers().values()]

print(lyrs)

extent = read_extent_from_file(relief_raster_path)

for fc in lyrs:
    if fc.type() != QgsMapLayer.VectorLayer:
        print(str(fc.name())+' is not vector data')
        continue
    print(fc.name())
    processing.run("qgis:definecurrentprojection", 
        {
        'INPUT':fc,
        'CRS':QgsCoordinateReferenceSystem(crs)
        })
        
    field_names = [field.name() for field in fc.fields()]
    if 'ELEV_ABS' in field_names:
        rastr_from_elev_field(fc)
        print('Height values from ELEV_ABS fields')
    else:
        print('Height values from RELIEF rastr values')
        postfix = '_relief_val'
        result_lyr = rastr_from_rastr_values(fc, extent, relief_raster_path, postfix)

print('RASTER by VECSTOR DATA was done succesfull')        

# MAKE RASTR TYPES       

def make_type_2A(base_rastr):
    iface.addRasterLayer(base_rastr, 'type_1B')
    extent = read_extent_from_file(base_rastr)
    result_1 = processing.run("qgis:rastercalculator", 
            {
            'EXPRESSION':'if("const_leaf_rastr_relief_val@1", "const_leaf_rastr_relief_val@1", "type_1B@1")',
            'LAYERS':[base_rastr],
            'CELLSIZE':2,
            'EXTENT':extent,
            'CRS':QgsCoordinateReferenceSystem(crs),
            'OUTPUT':'TEMPORARY_OUTPUT'
            })
    iface.addRasterLayer(result_1['OUTPUT'], 'temp')
    
    result_2 = processing.run("qgis:rastercalculator", 
            {
            'EXPRESSION':'if("tempo_leaf_rastr_relief_val@1", "tempo_leaf_rastr_relief_val@1", "temp@1")',
            'LAYERS':[base_rastr],
            'CELLSIZE':2,
            'EXTENT':extent,
            'CRS':QgsCoordinateReferenceSystem(crs),
            'OUTPUT':'Type_2A.tif'
            })
    remove_temp_lyr('temp')
    remove_temp_lyr('type_1B')
    return os.path.abspath(result_2['OUTPUT'])


def make_type_2B(base_rastr):
    type_2B = make_type_2B(base_rastr)
    
    iface.addRasterLayer(base_rastr, 'type_1B')
    result_1 = processing.run("qgis:rastercalculator", 
            {
            'EXPRESSION':'if("tempo_leaf_rastr_relief_val@1", "tempo_leaf_rastr_relief_val@1", "type_1B@1")',
            'LAYERS':[base_rastr],
            'CELLSIZE':2,
            'EXTENT':extent,
            'CRS':QgsCoordinateReferenceSystem(crs),
            'OUTPUT':'Type_2B.tif'
            })
    remove_temp_lyr('type_1B')
    
    return os.path.abspath(result_2['OUTPUT'])


def make_type_3A(base_rastr, type_2B, history):
    iface.addRasterLayer(base_rastr, 'type_1B')
    extent = read_extent_from_file(base_rastr)
    
    iface.addRasterLayer(history, 'history')
    iface.addRasterLayer(type_2B, 'type_2B')
    
    result_1 = processing.run("qgis:rastercalculator", 
            {
            'EXPRESSION':'if("history@1", "history@1", "type_2B@1")',
            'LAYERS':[base_rastr],
            'CELLSIZE':2,
            'EXTENT':extent,
            'CRS':QgsCoordinateReferenceSystem(crs),
            'OUTPUT':'Type_3A.tif'
            })

    remove_temp_lyr('history')
    remove_temp_lyr('type_2B')
    return os.path.abspath(result_1['OUTPUT'])



if make_type_rastrs is True:
    if os.path.isfile(const_leaf) is False:
        print('===== FILE with CONSTANTA leaf does not exists =====')
        raise Exception
    if os.path.isfile(tempo_leaf) is False:
        print('===== FILE with TEMPORARY leaf does not exists =====')
        raise Exception
    
    const_leaf_lyr = Qgs.VectorLayer(const_leaf)
    tempo_leaf_lyr = Qgs.VectorLayer(tempo_leaf)
    
    postfix = '_h_abs'
    const_leaf_rastr_h_abs = rastr_from_rastr_values(const_leaf, extent, leaf_rastr, postfix)
    tempo_leaf_rastr_h_abs = rastr_from_rastr_values(tempo_leaf, extent, leaf_rastr, postfix)
    const_leaf_rastr_h_abs.setName("const_leaf_rastr_h_abs")
    tempo_leaf_rastr_h_abs.setName("tempo_leaf_rastr_h_abs")
    
    postfix = '_relief_val'
    const_leaf_rastr_relief_val = rastr_from_rastr_values(const_leaf, extent, relief_raster_path, postfix)
    tempo_leaf_rastr_relief_val = rastr_from_rastr_values(tempo_leaf, extent, relief_raster_path, postfix)
    const_leaf_rastr_relief_val.setName("const_leaf_rastr_relief_val")
    tempo_leaf_rastr_relief_val.setName("tempo_leaf_rastr_relief_val")
    
    for r in kind_rastr_types:
        if r == 'Type_2A':
            if os.path.isfile(base_rastr) is False:
                print('===== FILE with BASE RASTR  Type_1B does not exists =====')  
            type_2A = make_type_2A(base_rastr)


        if r == 'Type_2B':
            if os.path.isfile(base_rastr) is False:
                print('===== FILE with BASE RASTR  Type_1B does not exists =====')
            type_2B = make_type_2B(base_rastr)


        if r == 'Type_3A':
            if os.path.isfile(base_rastr) is False:
                print('===== FILE with BASE RASTR  Type_1B does not exists =====')
            if os.path.isfile(history) is False:
                print('===== FILE with HISTORY does not exists =====')
            if type_2A is None:
                type_2A = make_type_2B(base_rastr)

            type_3A = make_type_2A(base_rastr, type_2A, history)
            
        if r == 'Type_3B':
            if os.path.isfile(base_rastr) is False:
                print('===== FILE with BASE RASTR  Type_1B does not exists =====')
            if os.path.isfile(history) is False:
                print('===== FILE with HISTORY does not exists =====')
            if type_2B is None:
                type_2B = make_type_2B(base_rastr)

            type_3B = make_type_2B(base_rastr, type_2B, history)
            
print('FINISH')        