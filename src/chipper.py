import os
import osr
import glob
import argparse
import geopandas as gpd
import shapely

from osgeo import gdal
from inventory import Inventory


class Chipper():

    # output formats
    _formats={  'jpg' : [ 'QUALITY=95' ], 
                'tif' : [ 'COMPRESS=LZW' ] }

    def __init__( self, args ):

        """
        constructor
        """

        # compute half crop offset
        self._crop2 = args.crop_size / 2
        return


    def process( self, args ):
    
        """
        constructor
        """

        # load polygons into geodataframe
        polygons = gpd.read_file( args.polygon_file )

        # search for images
        path = os.path.join( args.image_path, '**' )
        path = os.path.join( path, args.match )

        inventory = Inventory.get( glob.glob( path, recursive=True ) )
        #inventory.geometry = inventory.geometry.map(lambda polygon: shapely.ops.transform(lambda x, y: (y, x), polygon))

        # for each located image
        chips = []
        for image in inventory.itertuples():
            
            # get image srs
            src_srs=osr.SpatialReference()
            src_srs.ImportFromWkt( image.projection )

            # get image chips collocated with intersecting polygons 
            _minx, _miny, _maxx, _maxy = image.geometry.bounds
            intersects = polygons.cx[ _miny : _maxy, _minx : _maxx ]        
            
            for polygon in intersects.itertuples():

                # compute reprojected centroid location of intersecting polygon
                centroid = polygon.geometry.centroid
                coords = Inventory.reprojectCoordinates( [ ( centroid.y, centroid.x ) ], Inventory._geo_srs, src_srs )

                # get centroid image coordinates
                px = int( ( coords[ 0 ][ 0 ] - image.transform[0]) / image.transform[1] )
                py = int( ( coords[ 0 ][ 1 ] - image.transform[3]) / image.transform[5] )

                # define aoi around centroid location
                xoff = px - self._crop2; yoff = py - self._crop2
                if xoff >= 0 and yoff >= 0 and xoff + args.crop_size < image.cols and yoff + args.crop_size < image.rows:

                    # process all images with identical geometry 
                    matches = inventory [ inventory.geometry == image.geometry ]
                    for match in matches.itertuples():

                        # create filename                        
                        prefix = os.path.splitext ( os.path.basename( match.pathname ) )[ 0 ]
                        filename = 'chip_{image_id}_{polygon_id}_{crop}.{extension}'.format (   image_id=prefix,  
                                                                                                polygon_id=polygon.Index, 
                                                                                                crop=args.crop_size,
                                                                                                extension=args.format )

                        # create output file
                        out_pathname = os.path.join( args.out_path, 'images' )
                        out_pathname = os.path.join( out_pathname, filename )

                        if not os.path.exists( out_pathname ):

                            # create path if not exists
                            if not os.path.exists( os.path.dirname( out_pathname ) ):
                                os.makedirs( os.path.dirname( out_pathname ) )

                            # open original image
                            ds = gdal.Open( match.pathname )
                            if ds is not None:

                                # use gdal to crop image
                                out_ds = gdal.Translate(    out_pathname, 
                                                            ds, 
                                                            bandList=[1,2,3,4,5,6,7,8,9], 
                                                            srcWin = [xoff, yoff, args.crop_size, args.crop_size ], 
                                                            creationOptions=Chipper._formats[ args.format ] )

                                # flush buffer
                                chips.append( out_pathname )
                                out_ds = None


        # return inventory for newly created chips
        return Inventory.get( chips )

