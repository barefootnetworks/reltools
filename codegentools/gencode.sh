#!/bin/bash
cd $SR_CODE_BASE/reltools/codegentools/structs/
source env.sh
mkdir -p  $SR_CODE_BASE/reltools/codegentools/._genInfo
#pyang --plugindir `pwd` -f pybind  -o $SR_CODE_BASE/snaproute/src/models/objects/gen_stp.go $SR_CODE_BASE/snaproute/src/models/objects/yangmodel/stp/*.yang
# pyang --plugindir `pwd` -f pybind  -o $SR_CODE_BASE/snaproute/src/models/objects/gen_vxlan.go $SR_CODE_BASE/snaproute/src/models/objects/yangmodel/vxlan/*.yang
#pyang --plugindir `pwd` -f pybind  -o $SR_CODE_BASE/snaproute/src/models/objects/gen_lacp.go $SR_CODE_BASE/snaproute/src/models/objects/yangmodel/lacp/openconfig-if-aggregate.yang
pyang --plugindir `pwd` -f pybind  -o $SR_CODE_BASE/snaproute/src/models/objects/gen_ldp.go $SR_CODE_BASE/snaproute/src/models/objects/yangmodel/ldp/ldp.yang
cd $SR_CODE_BASE/reltools/codegentools/dbif/
./dbifGen.sh
cd $SR_CODE_BASE/reltools/codegentools/thrift
python thriftgen.py
for srcFile in `cat $SR_CODE_BASE/reltools/codegentools/._genInfo/generatedGoFiles.txt`;
do
if [[ $srcFile == *."go"* ]]
then
	   go fmt $srcFile
fi
done    
cd $SR_CODE_BASE/reltools/codegentools/apigen
python generateApis.py 

