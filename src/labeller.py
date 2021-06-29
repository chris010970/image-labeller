import os
import osr
import glob
import argparse
import geopandas as gpd

from osgeo import gdal, ogr

class Labeller():

    def __init__( self, args ):

        """
        constructor
        """

        # read polygons file
        self._polygons = gpd.read_file( args.polygon_file )

        # define default labels
        self._labels = [ 'object' ]
        if args.label is not None:
            
            # get unique labels
            self._labels = self._polygons[ args.label ].unique()

        return


    def process( self, inventory, args ):
    
        """
        constructor
        """

        # for each image
        out_path = os.path.join( args.out_path, 'labels' )
        for image in inventory.itertuples():

            # get polygons intersecting image geographic extent
            _minx, _miny, _maxx, _maxy = image.geometry.bounds
            intersects = self._polygons.cx[ _minx : _maxx, _miny : _maxy ]

            for label in self._labels:

                # default two labels
                if args.label is None:

                    # create mask for all intersecting polygons
                    self.getGeocodedMask(   image, 
                                            intersects,
                                            os.path.join( out_path, label ) )


        return


    def getGeocodedMask ( self, image, intersects, out_path, fill=0 ):

        """
        burn intersecting polygons onto 
        """

        # construct filename
        _, extension = os.path.splitext( image.pathname )
        filename = os.path.basename( image.pathname )
        filename = filename.replace( extension, '-mask.tif' )

        # delete label pathname if exists
        label_pathname = os.path.join( out_path, filename )
        if not os.path.exists( out_path ):
            os.makedirs( out_path )

        # create mask with lossless compression
        driver = gdal.GetDriverByName('GTiff')
        ds = driver.Create(     label_pathname, 
                                image.cols, 
                                image.rows, 
                                1, 
                                gdal.GDT_Byte, 
                                options=[ 'TILED=YES', 'COMPRESS=DEFLATE' ]  )

        if ds is not None:

            # copy image geocoding to mask
            ds.SetProjection( image.projection )
            ds.SetGeoTransform( image.transform )  
            ds.GetRasterBand(1).Fill( fill )

            # add polygon(s) to new label image
            self.addPolygonsToMask( ds, intersects, 255-fill )
            ds = None

        return


    def addPolygonsToMask( self, ds, intersects, value ):

        """
        burn shapefile into image buffer
        """

        # open exported dataframe in json format
        fid = ogr.Open( intersects.to_json() )
        layer = fid.GetLayer()

        # rasterize vector sub-region
        error = gdal.RasterizeLayer(    ds,            # output to our new dataset
                                        [1],           # output to our new dataset's first band
                                        layer,         # rasterize this layer
                                        None, None,    # don't worry about transformations since we're in same projection
                                        [value],           # burn value
                                        ['ALL_TOUCHED=TRUE' ]   # rasterize all pixels touched by polygons
                                        )
        ds.FlushCache()
        return

