# Scene inputs

Set PYLSTEMP_SCENE to one Landsat 8/9 Collection 2 Level-1 folder.
Required: B2, B4, B5, B10, B11, MTL.txt, QA_PIXEL and QA_RADSAT. Keep original product filenames.
SZA is used when available (hundredths of degrees). All rasters must be aligned.
No large scene data is committed. Notebooks use a calibrated 256x256 ROI.
For full-scene validation, run scripts/validate_scenes.py from the project root.
Examples also find scenes in Imagens/ within the project or ../Imagens/ beside this version folder.
