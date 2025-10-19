import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Play,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  FileText,
  BarChart3,
  Filter
} from "lucide-react";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import axiosInstance from "@/lib/axios";

interface TestRun {
  id: string;
  version: string | null;
  git_commit: string | null;
  started_at: string | null;
  completed_at: string | null;
  status: 'running' | 'passed' | 'failed' | 'error';
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  error_tests: number | null;
  coverage_pct: number;
  test_type: string;
  environment: string;
  duration_ms: number | null;
  triggered_by: string;
}

interface TestStats {
  total_runs: number;
  passed_runs: number;
  failed_runs: number;
  avg_coverage_pct: number;
  avg_duration_ms: number;
  avg_total_tests: number;
  avg_pass_rate_pct: number;
  period_days: number;
}

export default function TestDashboard() {
  const { toast } = useToast();
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [testStats, setTestStats] = useState<TestStats | null>(null);
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [currentTestRunId, setCurrentTestRunId] = useState<string | null>(null);
  const [selectedTestType, setSelectedTestType] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch test runs
  const fetchTestRuns = async () => {
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (selectedTestType !== 'all') params.test_type = selectedTestType;

      const response = await axiosInstance.get('/api/v1/tests/runs', { params });
      if (response.data.success) {
        setTestRuns(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching test runs:', error);
      toast({
        title: "Error",
        description: "Failed to fetch test runs",
        variant: "destructive",
      });
    }
  };

  // Fetch test statistics
  const fetchTestStats = async () => {
    try {
      const response = await axiosInstance.get('/api/v1/tests/stats', {
        params: { days: 7 }
      });
      if (response.data.success) {
        setTestStats(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching test stats:', error);
    }
  };

  // Run tests
  const runTests = async (testType: string = 'all') => {
    setIsRunningTests(true);
    try {
      const response = await axiosInstance.post('/api/v1/tests/run', {
        test_type: testType,
        version: null,
        git_commit: null,
      });

      if (response.data.success) {
        setCurrentTestRunId(response.data.test_run_id);
        toast({
          title: "Tests Started",
          description: response.data.message,
        });

        // Poll for results
        pollTestRun(response.data.test_run_id);
      }
    } catch (error: any) {
      console.error('Error running tests:', error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to start tests",
        variant: "destructive",
      });
      setIsRunningTests(false);
    }
  };

  // Poll test run status
  const pollTestRun = async (testRunId: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;

      try {
        const response = await axiosInstance.get(`/api/v1/tests/runs/${testRunId}`);
        const testRun: TestRun = response.data;

        if (testRun.status !== 'running') {
          clearInterval(poll);
          setIsRunningTests(false);
          setCurrentTestRunId(null);

          // Refresh test runs list
          await fetchTestRuns();
          await fetchTestStats();

          toast({
            title: testRun.status === 'passed' ? "Tests Passed" : "Tests Failed",
            description: `${testRun.passed_tests}/${testRun.total_tests} tests passed`,
            variant: testRun.status === 'passed' ? 'default' : 'destructive',
          });
        }

        if (attempts >= maxAttempts) {
          clearInterval(poll);
          setIsRunningTests(false);
          toast({
            title: "Timeout",
            description: "Test run is taking longer than expected",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('Error polling test run:', error);
      }
    }, 5000); // Poll every 5 seconds
  };

  // Initial data fetch
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchTestRuns(), fetchTestStats()]);
      setLoading(false);
    };
    fetchData();
  }, [statusFilter, selectedTestType]);

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any; label: string }> = {
      running: { variant: 'default', icon: RefreshCw, label: 'Running' },
      passed: { variant: 'default', icon: CheckCircle, label: 'Passed' },
      failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
      error: { variant: 'destructive', icon: AlertCircle, label: 'Error' },
    };

    const config = variants[status] || variants.error;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return 'N/A';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${seconds}s`;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen flex">
      <Sidebar />

      <main className="flex-1 overflow-hidden">
        <Header
          title="Test Dashboard"
          subtitle="Manage and monitor test execution across the platform"
        />

        <div className="p-6 h-full overflow-y-auto">
          {/* Summary Statistics */}
          {testStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total Runs (7d)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{testStats.total_runs}</div>
                  <p className="text-xs text-muted-foreground">
                    {testStats.passed_runs} passed, {testStats.failed_runs} failed
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Avg Coverage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{testStats.avg_coverage_pct.toFixed(1)}%</div>
                  <Progress value={testStats.avg_coverage_pct} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Avg Pass Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{testStats.avg_pass_rate_pct.toFixed(1)}%</div>
                  <Progress value={testStats.avg_pass_rate_pct} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Avg Duration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatDuration(testStats.avg_duration_ms)}</div>
                  <p className="text-xs text-muted-foreground">
                    ~{Math.round(testStats.avg_total_tests)} tests per run
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Test Control Panel */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Run Tests</CardTitle>
              <CardDescription>Execute test suites and monitor progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={() => runTests('all')}
                  disabled={isRunningTests}
                  className="btn-primary"
                >
                  <Play className="mr-2 h-4 w-4" />
                  Run All Tests
                </Button>
                <Button
                  onClick={() => runTests('api')}
                  disabled={isRunningTests}
                  variant="outline"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  API Tests
                </Button>
                <Button
                  onClick={() => runTests('auth')}
                  disabled={isRunningTests}
                  variant="outline"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Auth Tests
                </Button>
                <Button
                  onClick={() => runTests('algorithms')}
                  disabled={isRunningTests}
                  variant="outline"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Algorithm Tests
                </Button>
                <Button
                  onClick={() => runTests('integration')}
                  disabled={isRunningTests}
                  variant="outline"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Integration Tests
                </Button>
              </div>

              {isRunningTests && (
                <div className="mt-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Running tests... (ID: {currentTestRunId})
                  </div>
                  <Progress value={undefined} className="animate-pulse" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Test Run History */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Test Run History</CardTitle>
                  <CardDescription>View past test executions and results</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchTestRuns}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading test runs...</div>
              ) : testRuns.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No test runs found. Run your first test suite to get started!
                </div>
              ) : (
                <div className="space-y-4">
                  {testRuns.map((run) => (
                    <div
                      key={run.id}
                      className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {getStatusBadge(run.status)}
                            <Badge variant="outline">{run.test_type}</Badge>
                            <Badge variant="secondary">{run.environment}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Started: {formatDate(run.started_at)} by {run.triggered_by}
                          </p>
                          {run.git_commit && (
                            <p className="text-xs text-muted-foreground font-mono">
                              Commit: {run.git_commit.substring(0, 8)}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            {run.passed_tests}/{run.total_tests} passed
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Duration: {formatDuration(run.duration_ms)}
                          </p>
                        </div>
                      </div>

                      {/* Test Results Breakdown */}
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span>{run.passed_tests} Passed</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-500" />
                          <span>{run.failed_tests} Failed</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-yellow-500" />
                          <span>{run.skipped_tests} Skipped</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <BarChart3 className="h-4 w-4 text-blue-500" />
                          <span>{run.coverage_pct.toFixed(1)}% Coverage</span>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      {run.total_tests > 0 && (
                        <div className="mt-3">
                          <Progress
                            value={(run.passed_tests / run.total_tests) * 100}
                            className="h-2"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
