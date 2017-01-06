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
gProto = ''

def _askDetails():
    global gAnchorDir, gGitUsrName, gRole, gProto
    gAnchorDir = prompt('Host directory:', default='git')
    gGitUsrName = prompt('Git username:')
    gProto = prompt('Git Protocol (https/ssh):', default='https')
    gRole = prompt('SnapRoute Employee (y/n):', default='n')

def setupHandler():
    global gAnchorDir, gGitUsrName, gRole
    if '' in [gAnchorDir, gGitUsrName, gRole]:
        _askDetails()
    return getSetupHdl('setupInfo.json', gAnchorDir, gGitUsrName, gRole)

def setupExternals(comp=None):
    print 'Installing all External dependencies....'
    info = setupHandler().getExternalInstalls(comp)
    for comp, deps in info.iteritems():
        print 'Installing dependencies for %s' % (comp)
        for dep in deps:
            cmd = 'sudo apt-get install -y ' + dep
            with settings(prompts={'Do you want to continue [Y/n]? ': 'Y'}):
                local(cmd)

def setupCliDeps(gitProto='http'):
    print 'Fetching Python dependencies for CLI....'
    usrName = setupHandler().getUsrName()
    if gitProto == 'ssh':
        userRepoPrefix   = 'git@github.com:%s/' % (usrName)
        remoteRepoPrefix = 'git@github.com:%s/' % ('OpenSnaproute')
    else:
#        userRepoPrefix = 'https://github.com/%s/' % (usrName)
#        remoteRepoPrefix = 'https://github.com/%s/' % ('OpenSnaproute')
        userRepoPrefix = 'https://github.com/%s/' % ('barefootnetworks')
        remoteRepoPrefix = 'https://github.com/OpenSnaproute/'
    _setupGitRepo('extPkgs',
                    setupHandler().getExtSrcDir(),
                    userRepoPrefix,
                    remoteRepoPrefix)

def _setupGitRepo(repo, srcDir, userRepoPrefix, remoteRepoPrefix):
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

def _getRepoUrlPrefix(proto='http'):
    internalUser = setupHandler().getUsrRole()
    usrName = setupHandler().getUsrName()
    org = setupHandler().getOrg()
    gitProto = setupHandler().getGitProto()

    if gitProto == 'ssh':
        if not internalUser:
            userRepoPrefix   = 'git@github.com:%s/' % (org)
        else:
            userRepoPrefix   = 'git@github.com:%s/' % (usrName)
    else:
        if not internalUser:
            userRepoPrefix   = 'https://github.com/%s/' % (org)
        else:
            userRepoPrefix   = 'https://github.com/%s/' % (usrName)
    return userRepoPrefix

def _getRepoRemoteUrlPrefix(proto='http'):
    internalUser = setupHandler().getUsrRole()
    org = setupHandler().getOrg()
    gitProto = setupHandler().getGitProto()

    remoteRepoPrefix = None
    if gitProto == 'ssh':
        if internalUser:
            remoteRepoPrefix = 'git@github.com:%s/' % (org)
    else:
        if internalUser:
            remoteRepoPrefix = 'https://github.com/%s/' % (org)

    return remoteRepoPrefix

def setupGoDeps(comp=None, gitProto='http'):
    print 'Fetching external  Golang repos ....'
    info = setupHandler().getGoDeps(comp)
    extSrcDir = setupHandler().getExtSrcDir()
    org = setupHandler().getOrg()
    for rp in info:
        with lcd(extSrcDir):
            if gitProto == "ssh":
                repoUrl = 'git@github.com:%s/%s' % (org, rp['repo'])
            else:
                repoUrl = 'https://github.com/%s/%s' % (org, rp['repo'])
            dstDir = rp['renamedst'] if rp.has_key('renamedst') else ''
            dirToMake = dstDir
            cloned = False
            if not os.path.exists(extSrcDir+ dstDir + '/' + rp['repo']):
                cmd = 'git clone ' + repoUrl
                local(cmd)
                cloned = True
                if rp.has_key('reltag'):
                    cmd = 'git checkout tags/'+ rp['reltag']
                    with lcd(extSrcDir+rp['repo']):
                        local(cmd)

            if not dstDir.endswith('/'):
                dirToMake = dstDir[0:dstDir.rfind('/')]
            if dirToMake:
                cmd = 'mkdir -p ' + dirToMake
                local(cmd)
            if rp.has_key('renamesrc') and cloned:
                cmd = 'mv ' + extSrcDir+ rp['renamesrc']+ ' ' + extSrcDir+ rp['renamedst']
                local(cmd)

def setupSRRepos(gitProto='http', comp=None):
    print 'Fetching Snaproute repositories dependencies....'
    global gAnchorDir, gGitUsrName, gRole
    gAnchorDir = prompt('Host directory:', default='git')
    gGitUsrName = prompt('Git username:')
    gRole = prompt('SnapRoute Employee (y/n):', default='n')
    if comp:
        srRepos = [comp]
    else:
        srRepos = setupHandler().getSRRepos()
    org = setupHandler().getOrg()
    pkgRepoOrg = setupHandler().getPkgRepoOrg()
    internalUser = setupHandler().getUsrRole()
    usrName = setupHandler().getUsrName()
    srcDir = setupHandler().getSRSrcDir()
    anchorDir = setupHandler().getAnchorDir()
    srPkgRepos = setupHandler().getSRPkgRepos()

    if not os.path.isfile(srcDir+'/Makefile'):
        cmd = 'ln -s ' + anchorDir+  '/reltools/Makefile '+  srcDir + 'Makefile'
        local(cmd)
    if gitProto == "ssh":
        if not internalUser:
            userRepoPrefix   = 'git@github.com:%s/' % (org)
            remoteRepoPrefix = None
            pkgRepoPrefix = 'git@github.com:%s/' % (pkgRepoOrg)
        else:
            userRepoPrefix   = 'git@github.com:%s/' % (usrName)
            remoteRepoPrefix = 'git@github.com:%s/' % (org)
    else:
        if not internalUser:
            userRepoPrefix   = 'https://github.com/%s/' % (org)
            remoteRepoPrefix = None
            pkgRepoPrefix = 'https://github.com/%s/' % (pkgRepoOrg)
        else:
            userRepoPrefix   = 'https://github.com/%s/' % (usrName)
            remoteRepoPrefix = 'https://github.com/%s/' % (org)

    for repo in srRepos:
        with lcd(srcDir):
            if not (os.path.exists(srcDir + repo)  and os.path.isdir(srcDir+ repo)):
                if repo in srPkgRepos:
                    prefix = pkgRepoPrefix
                else:
                    prefix = userRepoPrefix
                cmd = 'git clone '+ prefix + repo
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
            LFSRepos = setupHandler().getLFSEnabledRepos()
            if repo in LFSRepos:
                with lcd(srcDir + repo):
                    commandsToCheckout = [
                            'git lfs fetch',
                            'git lfs checkout'
                            ]
#                    for cmd in commandsToCheckout:
#                        local(cmd)
def installThrift():
    TMP_DIR = ".tmp"
    thriftVersion = '0.9.3'
    thriftPkgName = 'thrift-' + thriftVersion
    if _verifyThriftInstallation(thriftVersion):
        print 'Thrift Already installed. Skipping installation'
        return

    thrift_tar = thriftPkgName +'.tar.gz'
    local('mkdir -p ' + TMP_DIR)
    local('wget -O ' + TMP_DIR + '/' + thrift_tar + ' ' + 'http://www-us.apache.org/dist/thrift/0.9.3/thrift-0.9.3.tar.gz')

    with lcd(TMP_DIR):
        local('tar -xvf ' + thrift_tar)
        with lcd(thriftPkgName):
            local('./configure --with-java=false')
            local('make')
            local('sudo make install')


def installNanoMsgLib():
    srcDir = setupHandler().getGoDepDirFor('nanomsg')
    with lcd(srcDir):
        cmdList = ['sudo apt-get install -y libtool',
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
                cmdList.append('./configure')
            elif lib == 'libnftnl':
                #os.environ["LIBMNL_CFLAGS"]= nfLoc + libipDir + "/include/libmnl"
                #os.environ["LIBMNL_LIBS"]= nfLoc + libipDir + "/lib/pkgconfig"
                cmdList.append('./configure')
            elif lib == 'iptables':
                cmdList.append('./configure')
            cmdList.append('make')
            cmdList.append('sudo make install')
            for cmd in cmdList:
                local(cmd)

def _createDirectoryStructure():
    dirs = setupHandler().getAllSrcDir()
    for everydir in dirs:
        local('mkdir -p '+ everydir)

def _verifyThriftInstallation(thriftVersion='0.9.3'):
    with settings(warn_only=True):
        ret = local('which thrift', capture=True)
        if ret.failed:
            return False
    resp = local('thrift -version', capture=True)
    return thriftVersion in resp

def printInstruction():
    print "###########################"
    print "Please add the following lines in your ~/.bashrc file"
    print "###########################"
    print "export PATH=$PATH:/usr/local/go/bin"
    print "export SR_CODE_BASE=$HOME/git"
    print "export GOPATH=$SR_CODE_BASE/snaproute/:$SR_CODE_BASE/external/:$SR_CODE_BASE/generated/"
    print "###########################"

def setupDevEnv():
    _askDetails()
    local('git config --global credential.helper \"cache --timeout=3600\"')
    _createDirectoryStructure()
    setupHandler()
    setupExternals()
    setupCliDeps(gitProto=gProto)
    setupGoDeps(gitProto=gProto)
    installThrift()
    installNanoMsgLib()
    installIpTables()
    setupSRRepos(gitProto=gProto)
    printInstruction()

def pushDocker(repo='flex1'):
    print "Push the latest docker image to docker hub"
    print "Keep the usermane and password for dockerhub ready."
    local('docker login')
    cmd = "docker push snapos/flex:"+repo
    local(cmd)
    print "Success..."
