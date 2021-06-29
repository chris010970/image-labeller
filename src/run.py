import os
import sys
import argparse
import geopandas as gpd

from chipper import Chipper
from labeller import Labeller

#import glob
#from inventory import Inventory


def parseArguments(args=None):

    """
    parse command line argument
    """

    # parse command line arguments
    parser = argparse.ArgumentParser(description='labeller')

    parser.add_argument('image_path', action="store")
    parser.add_argument('polygon_file', action="store")
    parser.add_argument('out_path', action="store")

    # crop size
    parser.add_argument(    '--crop_size', 
                            type=int,
                            action='store',
                            default=256 )

    # image match string
    parser.add_argument(    '--match', 
                            type=str,
                            action='store',
                            default='*.TIF' )

    # polygon class attribute string
    parser.add_argument(    '--label', 
                            type=str,
                            action='store',
                            default=None )

    # output format string
    parser.add_argument(    '--format', 
                            choices=Chipper._formats.keys(),
                            action='store',
                            default='jpg' )

    return parser.parse_args(args)


def main():

    """
    main path of execution
    """

    # parse arguments
    args = parseArguments()   

    # validate optional label argument
    if args.label is not None:
        polygons = gpd.read_file( args.polygon_file )
        if args.label not in list( polygons.columns ):
            sys.exit ( 'Label attribute {label} not present in file {pathname}'.format( label=args.label,
                                                                                        pathname=args.polygon_file ) )
    
    # create and run chipper    
    chipper = Chipper( args )
    chips = chipper.process( args )

    #path = 'C:\\Users\\Chris.Williams\\Desktop\\chips\\*.jpg'
    #chips = Inventory.get( glob.glob( path, recursive=True ) )

    # create label masks
    labeller = Labeller( args )
    labeller.process( chips, args )

    return


# execute main
if __name__ == '__main__':
    main()
