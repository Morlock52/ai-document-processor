'use client';

import { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentUploader } from '@/components/document-uploader';
import { DocumentList } from '@/components/document-list';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  FileText,
  Zap,
  Download,
  ArrowRight,
  Sparkles,
  Table,
  ToggleLeft,
  ToggleRight,
  ShieldCheck,
  KeyRound,
  Lock,
  Unlock,
  RotateCcw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { authApi, type ApiError } from '@/lib/api';
import type { AuthStatus } from '@/types';
import { useToast } from '@/hooks/use-toast';

export default function Home() {
  const { toast } = useToast();
  const [templateMode, setTemplateMode] = useState(false);
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passcodeInput, setPasscodeInput] = useState('');
  const [confirmPasscode, setConfirmPasscode] = useState('');
  const [loginPasscode, setLoginPasscode] = useState('');
  const [isUpdatingLogin, setIsUpdatingLogin] = useState(false);
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await authApi.status();
        setAuthStatus(status);

        const storedToken = authApi.getStoredToken();
        if (!status.require_login || storedToken) {
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Failed to load authentication status', error);
        toast({
          title: 'Access control check failed',
          description: 'Using open mode until settings load.',
          variant: 'destructive',
        });
        setIsAuthenticated(true);
      } finally {
        setAuthChecked(true);
      }
    };

    void loadStatus();
  }, [toast]);

  const handleLogin = async () => {
    setIsSigningIn(true);
    setLoginError('');

    try {
      await authApi.login(loginPasscode);
      setIsAuthenticated(true);
      setLoginPasscode('');
      toast({ title: 'Welcome back', description: 'Login enabled features are unlocked.' });
    } catch (error) {
      const apiError = error as ApiError;
      const message = apiError.userMessage || apiError.message || 'Invalid passcode';
      setLoginError(message);
      toast({ title: 'Login failed', description: message, variant: 'destructive' });
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleToggleLogin = async (nextState: boolean) => {
    if (nextState) {
      if (!passcodeInput || passcodeInput.length < 6) {
        toast({
          title: 'Passcode too short',
          description: 'Use at least 6 characters so the lock is meaningful.',
          variant: 'destructive',
        });
        return;
      }

      if (passcodeInput !== confirmPasscode) {
        toast({
          title: 'Passcodes do not match',
          description: 'Enter the same value twice to avoid lockouts.',
          variant: 'destructive',
        });
        return;
      }
    }

    setIsUpdatingLogin(true);
    try {
      const status = await authApi.updateLogin(nextState, nextState ? passcodeInput : undefined);
      setAuthStatus(status);
      setIsAuthenticated(!status.require_login);
      setPasscodeInput('');
      setConfirmPasscode('');
      toast({
        title: status.require_login ? 'Login protection enabled' : 'Login protection disabled',
        description: status.require_login
          ? 'Users will now need the passcode before processing documents.'
          : 'Workspace access is open again.',
      });
    } catch (error) {
      const apiError = error as ApiError;
      toast({
        title: 'Could not update login setting',
        description: apiError.userMessage || apiError.message || 'Try again in a moment.',
        variant: 'destructive',
      });
    } finally {
      setIsUpdatingLogin(false);
    }
  };

  const lockActive = authStatus?.require_login === true && !isAuthenticated;
  const apiReady = authStatus ? (!authStatus.require_login || isAuthenticated) : false;

  const handleAuthReset = () => {
    setIsAuthenticated(false);
    setLoginPasscode('');
    setLoginError('Session expired or locked. Sign in again.');
  };

  return (
    <div className="space-y-12">
      {authChecked && lockActive && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <Card className="w-full max-w-xl border-0 shadow-2xl">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                  <Lock className="w-6 h-6" />
                </div>
                <div>
                  <CardTitle className="text-2xl">Login required</CardTitle>
                  <CardDescription>
                    Enter the shared passcode you configured in Settings to unlock document processing.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-200">Access passcode</label>
                <input
                  type="password"
                  value={loginPasscode}
                  onChange={(e) => setLoginPasscode(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter the passcode you saved"
                />
                {loginError && <p className="mt-2 text-sm text-red-500">{loginError}</p>}
              </div>
              <div className="flex gap-3">
                <Button
                  size="lg"
                  className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                  onClick={handleLogin}
                  disabled={isSigningIn || !loginPasscode.trim()}
                >
                  <ShieldCheck className="w-4 h-4 mr-2" /> Unlock workspace
                </Button>
                <Button variant="outline" size="lg" onClick={() => setLoginPasscode('')}>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Clear
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Lost the passcode? Disable login from the server console by setting <code>require_login</code> to false using the new /auth/settings/login endpoint.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-blue-950/20 dark:via-indigo-950/20 dark:to-purple-950/20 p-8 md:p-12">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25"></div>
        <div className="relative">
          <div className="flex items-center gap-2 mb-6">
            <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="px-3 py-1 text-sm font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full">
              AI-Powered Processing
            </div>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-gray-900 via-indigo-800 to-purple-800 dark:from-white dark:via-indigo-200 dark:to-purple-200 bg-clip-text text-transparent mb-6">
            Transform PDFs into
            <br />
            <span className="text-indigo-600 dark:text-indigo-400">Structured Data</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl leading-relaxed">
            Upload any PDF document and watch our AI extract, organize, and export your data to Excel in seconds. No manual data entry required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" className="text-base px-8 py-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300">
              Get Started
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button variant="outline" size="lg" className="text-base px-8 py-6 rounded-2xl border-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-300">
              View Demo
            </Button>
          </div>
        </div>
      </div>

      {/* Template Mode Toggle */}
      <Card className="border-0 shadow-lg rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/20 dark:to-teal-950/20">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
                <Table className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Template Mode</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Automatically create Excel columns from detected fields and aggregate all scanned data
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="lg"
              onClick={() => setTemplateMode(!templateMode)}
              className={`flex items-center gap-2 px-6 py-3 rounded-2xl transition-all duration-300 ${
                templateMode
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              {templateMode ? (
                <>
                  <ToggleRight className="w-5 h-5" />
                  <span className="font-medium">Enabled</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="w-5 h-5" />
                  <span className="font-medium">Disabled</span>
                </>
              )}
            </Button>
          </div>
          {templateMode && (
            <div className="mt-4 p-4 bg-emerald-100 dark:bg-emerald-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-emerald-700 dark:text-emerald-300">
                  <p className="font-medium mb-1">Template Mode Active</p>
                  <ul className="space-y-1 text-xs">
                    <li>• All detected fields will become Excel columns</li>
                    <li>• Each scanned document will be a new row</li>
                    <li>• Download consolidated Excel with all data</li>
                    <li>• Toggle off to return to individual document mode</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-0 shadow-lg rounded-2xl bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-indigo-950/20 dark:via-gray-950/40 dark:to-purple-950/20">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                {authStatus?.require_login ? <Lock className="w-6 h-6" /> : <Unlock className="w-6 h-6" />}
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Access control</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Login is optional on first install. Turn it on once you have set (and confirmed) a passcode.
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-gray-500">Status</p>
              <p className="font-semibold text-indigo-700 dark:text-indigo-300">
                {authStatus?.require_login ? 'Protected' : 'Open by default'}
              </p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-200">Set passcode (enter twice)</label>
              <input
                type="password"
                value={passcodeInput}
                onChange={(e) => setPasscodeInput(e.target.value)}
                className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Create a workspace passcode"
              />
              <input
                type="password"
                value={confirmPasscode}
                onChange={(e) => setConfirmPasscode(e.target.value)}
                className="w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Confirm the passcode"
              />
              <p className="text-xs text-muted-foreground">
                Two matching entries help prevent typos and aligns with the request to configure it in two steps.
              </p>
            </div>

            <div className="space-y-3 p-4 rounded-2xl bg-white/70 dark:bg-gray-900/60 border border-dashed border-indigo-200 dark:border-indigo-900">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-200">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold">How it works</p>
                  <p className="text-sm text-muted-foreground">Disabled on first install; toggle to require a shared passcode once you have two matching entries.</p>
                </div>
              </div>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li>Passcode is stored securely server-side.</li>
                <li>All document and schema endpoints respect the lock.</li>
                <li>Disable anytime to return to open mode.</li>
              </ul>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => handleToggleLogin(true)}
                  disabled={isUpdatingLogin}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                >
                  <ShieldCheck className="w-4 h-4 mr-2" /> Enable login
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleToggleLogin(false)}
                  disabled={isUpdatingLogin || !authStatus?.require_login}
                >
                  <Unlock className="w-4 h-4 mr-2" /> Disable login
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="upload" className="space-y-8">
        <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 h-12 p-1 bg-gray-100 dark:bg-gray-800 rounded-2xl">
          <TabsTrigger value="upload" className="rounded-xl font-medium data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm transition-all duration-200">
            <FileText className="w-4 h-4 mr-2" />
            Upload
          </TabsTrigger>
          <TabsTrigger value="documents" className="rounded-xl font-medium data-[state=active]:bg-white dark:data-[state=active]:bg-gray-700 data-[state=active]:shadow-sm transition-all duration-200">
            <Download className="w-4 h-4 mr-2" />
            Documents
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-8">
          <Card className="border-0 shadow-xl rounded-3xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
            <CardHeader className="pb-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className="text-2xl font-bold">Upload Your Documents</CardTitle>
                  <CardDescription className="text-base mt-1">
                    Drag & drop PDF files or click to browse. Our AI will handle the rest.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <DocumentUploader templateMode={templateMode} canUpload={apiReady} />
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl rounded-3xl bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-center mb-2">How It Works</CardTitle>
              <CardDescription className="text-center text-base">
                Three simple steps to extract your data
              </CardDescription>
            </CardHeader>
            <CardContent className="p-8">
              <div className="grid gap-8 md:grid-cols-3">
                <div className="text-center group">
                  <div className="relative mb-6">
                    <div className="flex h-16 w-16 items-center justify-center mx-auto rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105">
                      <FileText className="w-8 h-8" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg">
                      1
                    </div>
                  </div>
                  <h3 className="text-xl font-bold mb-3">Upload PDFs</h3>
                  <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                    Simply drag and drop your PDF files or click to browse. We support batch uploads for efficiency.
                  </p>
                </div>
                <div className="text-center group">
                  <div className="relative mb-6">
                    <div className="flex h-16 w-16 items-center justify-center mx-auto rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 text-white shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105">
                      <Zap className="w-8 h-8" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-pink-400 to-red-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg">
                      2
                    </div>
                  </div>
                  <h3 className="text-xl font-bold mb-3">AI Processing</h3>
                  <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                    Our advanced GPT-4o model analyzes each page and intelligently extracts structured data.
                  </p>
                </div>
                <div className="text-center group">
                  <div className="relative mb-6">
                    <div className="flex h-16 w-16 items-center justify-center mx-auto rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105">
                      <Download className="w-8 h-8" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg">
                      3
                    </div>
                  </div>
                  <h3 className="text-xl font-bold mb-3">Export to Excel</h3>
                  <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                    Download your extracted data as beautifully formatted Excel spreadsheets, ready to use.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card className="border-0 shadow-xl rounded-3xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
            <CardHeader className="pb-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                  <Download className="w-5 h-5" />
                </div>
                <div>
                  <CardTitle className="text-2xl font-bold">Your Documents</CardTitle>
                  <CardDescription className="text-base mt-1">
                    Track processing status and download your extracted data.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <DocumentList templateMode={templateMode} enabled={apiReady} onAuthError={handleAuthReset} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}