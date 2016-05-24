import os
from fabric.api import local, run, env
from fabric.context_managers import lcd
from fabric.operations import prompt
from fabric.context_managers import settings
from setupTool import  setupGenie, getSetupHdl

env.use_ssh_config = True
gAnchorDir = ''
gGitUsrName = ''
gRole = ''

def setupHandler():
    global gAnchorDir, gGitUsrName, gRole
    return getSetupHdl('setupInfo.json', gAnchorDir, gGitUsrName, gRole)

def setupExternals (comp=None):
    info = setupHandler().getExternalInstalls(comp)
    for comp, deps in info.iteritems(): 
        print 'Installing dependencies for %s' %(comp)
        for dep in deps:
            cmd = 'sudo apt-get install ' + dep
    	    with settings(prompts={'Do you want to continue [Y/n]? ': 'Y'}):
                local(cmd)

def setupGoDeps(comp=None, gitProto='http'):
    info = setupHandler().getGoDeps(comp)
    extSrcDir = setupHandler().getExtSrcDir()
    print extSrcDir
    org = setupHandler().getOrg()
    for rp in info:
        with lcd(extSrcDir):
            print rp
            if gitProto == "ssh":
                repoUrl = 'git@github.com:%s/%s' %(org , rp['repo'])
            else:
                repoUrl = 'https://github.com/%s/%s' %(org , rp['repo'])
            print repoUrl
            dstDir =  rp['renamedst'] if rp.has_key('renamedst') else ''
            dirToMake = dstDir 
            if dstDir == '' or (dstDir != '' and not (os.path.exists(extSrcDir+ dstDir + '/' + rp['repo']))):
                cmd = 'git clone '+ repoUrl
                local(cmd)
                if rp.has_key('reltag'):
                    cmd = 'git checkout tags/'+ rp['reltag']
                    with lcd(extSrcDir+rp['repo']):
                        local(cmd)

            if not dstDir.endswith('/'):
                dirToMake = dstDir[0:dstDir.rfind('/')]
            if dirToMake:
                cmd  =  'mkdir -p ' + dirToMake
                local(cmd)
            if rp.has_key('renamesrc'):
                cmd = 'mv ' + extSrcDir+ rp['renamesrc']+ ' ' + extSrcDir+ rp['renamedst']
                local(cmd)

def setupSRRepos( gitProto = 'http' , comp = None):
    srRepos = setupHandler().getSRRepos()
    org = setupHandler().getOrg()
    internalUser =  setupHandler().getUsrRole()
    usrName =  setupHandler().getUsrName()
    srcDir = setupHandler().getSRSrcDir()
    anchorDir = setupHandler().getAnchorDir()

    if not os.path.isfile(srcDir+'/Makefile' ):
        cmd = 'ln -s ' + anchorDir+  '/reltools/Makefile '+  srcDir + 'Makefile'
        local(cmd)
    if gitProto == "ssh":
        if not internalUser:
            userRepoPrefix   = 'git@github.com:%s/' %(org)
            remoteRepoPrefix = None
        else:
            userRepoPrefix   = 'git@github.com:%s/' %(usrName)
            remoteRepoPrefix = 'git@github.com:%s/' %(org)
    else:
        if not internalUser:
            userRepoPrefix   = 'https://github.com/%s/' %(org)
            remoteRepoPrefix = None
        else:
            userRepoPrefix   = 'https://github.com/%s/' % (usrName)
            remoteRepoPrefix = 'https://github.com/%s/' % (org)

    for repo in srRepos:
        with lcd(srcDir):
            if not (os.path.exists(srcDir + repo)  and os.path.isdir(srcDir+ repo)):
                cmd = 'git clone '+ userRepoPrefix + repo 
                local(cmd)
            if remoteRepoPrefix:
                with lcd(srcDir +repo):
                    cmd = 'git remote add upstream ' + remoteRepoPrefix + repo + '.git'
                    local(cmd)
                    commandsToSync = ['git fetch upstream',
                                    'git checkout master',
                                    'git merge upstream/master']
                    for cmd in commandsToSync:
                        local(cmd)
def installThrift():
    TMP_DIR = ".tmp"
    thrift_version = '0.9.3'
    thrift_pkg_name = 'thrift-'+thrift_version 
    thrift_tar = thrift_pkg_name +'.tar.gz'
    local('mkdir -p '+TMP_DIR)
    local('wget -O '+ TMP_DIR + '/' +thrift_tar+ ' '+ 'http://www-us.apache.org/dist/thrift/0.9.3/thrift-0.9.3.tar.gz')
    
    with lcd(TMP_DIR):
        local('tar -xvf '+ thrift_tar)
        with lcd (thrift_pkg_name):
            local ('./configure --with-java=false')
            local ('make')
            local ('sudo make install')
        

def installNanoMsgLib ():
    srcDir = setupHandler().getGoDepDirFor('nanomsg')
    with lcd(srcDir):
        cmdList = ['sudo apt-get install libtool',
                'libtoolize',
                './autogen.sh',
                './configure',
                'make',
                'sudo make install',
                ]
        for cmd in cmdList:
            local(cmd)

def installIpTables():
    extSrcDir = setupHandler().getExtSrcDir()
    nfLoc = extSrcDir + 'github.com/netfilter/'
    libipDir = 'libiptables'
    allLibs = ['libmnl', 'libnftnl', 'iptables']
    prefixDir = nfLoc + libipDir
    cflagsDir = nfLoc + libipDir + "/include"
    ldflagsDir = nfLoc + libipDir + "/lib"

    for lib in allLibs:
        with lcd(nfLoc + lib):
            cmdList = []
            cmdList.append('./autogen.sh')
            if lib == 'libmnl':
                cmdList.append('./configure --prefix=\"' + prefixDir + '\"')
            elif lib == 'libnftnl':
                os.environ["LIBMNL_CFLAGS"]= nfLoc + libipDir + "/include/libmnl"
                os.environ["LIBMNL_LIBS"]= nfLoc + libipDir + "/lib/pkgconfig"
                cmdList.append('./configure --prefix="' + prefixDir + '" CFLAGS="-I' + cflagsDir + '" LDFLAGS="-L' + ldflagsDir +'"')
            elif lib == 'iptables':
                cmdList.append('./configure --prefix="' + prefixDir + '" CFLAGS="-I' + cflagsDir + '" LDFLAGS="-L' + ldflagsDir +'" LIBS=\"-lmnl -lnftnl\"')
            cmdList.append('make')
            cmdList.append('make install')
            for cmd in cmdList:
                local(cmd)

def _createDirectoryStructure() :
    dirs = setupHandler().getAllSrcDir()
    for everydir in dirs:
        local('mkdir -p '+ everydir) 

def setupDevEnv() :
    global gAnchorDir, gGitUsrName, gRole
    gAnchorDir = prompt('Host directory:', default='git')
    gGitUsrName = prompt('Git username:')
    gRole = prompt('SnapRoute Employee (y/n):', default='n')
    local('git config --global credential.helper \"cache --timeout=3600\"')
    _createDirectoryStructure()
    setupHandler()
    setupExternals()
    setupGoDeps()
    installThrift()
    installNanoMsgLib()
    installIpTables()
    setupSRRepos()
     
