# Конструктор растров
# Преполагается, что ограничивающие веторные данные
# загружены в проект.
# Поле в котором указаны ограничивающие высоты ELEV_ABS
import os
import processing

os.chdir(r'D:\Also\Genplan\Vector')

relief_raster_path = r'D:\Also\Genplan\_rastrs\!_Type1A_2023.tif'
crs = 'USER:100020'

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

    
def rastr_from_relief_rastr_values(name, extent):
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
    iface.addRasterLayer(relief_raster_path, 'relief')
    
    processing.run("gdal:assignprojection", 
            {
            'INPUT':'temp_rastr_555',
            'CRS':QgsCoordinateReferenceSystem(crs)
            })
    
    output_rast = processing.run("qgis:rastercalculator", 
                    {
                    'EXPRESSION':'if("temp_rastr_555@1"=555, "relief@1", 999)',
                    'LAYERS':[relief_raster_path],
                    'CELLSIZE':2,
                    'EXTENT':extent,
                    'CRS':QgsCoordinateReferenceSystem(crs),
                    'OUTPUT':name.name()+'_relief.tif'
                    })

    iface.addRasterLayer(output_rast['OUTPUT'], str(name.name()+'_relief'))
    remove_temp_lyr('temp_rastr_555')


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
        rastr_from_relief_rastr_values(fc, extent)
        
print('FINISH')        