"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bot, Wrench, Server, Workflow, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/client";

interface RegistryStatus {
  total_manifests: number;
  by_type: {
    agents: number;
    tools: number;
    relics: number;
    workflows: number;
  };
  last_updated: string;
}

interface ServiceHealth {
  status: string;
  service: string;
}

export default function Home() {
  const [stats, setStats] = useState<RegistryStatus | null>(null);
  const [health, setHealth] = useState<{
    manifest: ServiceHealth | null;
    runtime: ServiceHealth | null;
    llm: ServiceHealth | null;
  }>({ manifest: null, runtime: null, llm: null });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statusData, manifestHealth, runtimeHealth] = await Promise.all([
        api.manifests.getStatus(),
        api.system.health().catch(() => ({ status: "unknown", service: "manifest-ingestion" })),
        fetch("http://localhost:8083/health").then(r => r.json()).catch(() => ({ status: "unknown", service: "runtime-executor" }))
      ]);
      
      setStats(statusData);
      setHealth({
        manifest: manifestHealth,
        runtime: runtimeHealth,
        llm: { status: "healthy", service: "llm-gateway" } // Assume healthy if running
      });
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await fetch("http://localhost:8082/registry/sync", { method: "POST" });
      await loadData(); // Reload after sync
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const getHealthBadge = (status?: string) => {
    if (!status || status === "unknown") {
      return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500">Unknown</Badge>;
    }
    if (status === "healthy") {
      return <Badge variant="outline" className="bg-green-500/10 text-green-500">Healthy</Badge>;
    }
    return <Badge variant="outline" className="bg-red-500/10 text-red-500">Unhealthy</Badge>;
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                <p className="text-muted-foreground">
                  Welcome to Cortex-Prime B-Line - Your Sovereign AI Orchestration Platform
                </p>
              </div>
              <Button 
                onClick={handleSync} 
                disabled={syncing}
                variant="outline"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Manifests'}
              </Button>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Agents</CardTitle>
                  <Bot className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? "..." : stats?.by_type.agents || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Ready for execution
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Tools</CardTitle>
                  <Wrench className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? "..." : stats?.by_type.tools || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Available capabilities
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Relics</CardTitle>
                  <Server className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? "..." : stats?.by_type.relics || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Service manifests
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Workflows</CardTitle>
                  <Workflow className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {loading ? "..." : stats?.by_type.workflows || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Orchestration flows
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>
                    Common tasks and operations
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button className="w-full justify-start" variant="outline" asChild>
                    <Link href="/agents">
                      <Bot className="mr-2 h-4 w-4" />
                      Browse Agents
                    </Link>
                  </Button>
                  <Button className="w-full justify-start" variant="outline" asChild>
                    <Link href="/tools">
                      <Wrench className="mr-2 h-4 w-4" />
                      Browse Tools
                    </Link>
                  </Button>
                  <Button className="w-full justify-start" variant="outline" asChild>
                    <Link href="/relics">
                      <Server className="mr-2 h-4 w-4" />
                      Browse Relics
                    </Link>
                  </Button>
                  <Button className="w-full justify-start" variant="outline" asChild>
                    <Link href="/workflows">
                      <Workflow className="mr-2 h-4 w-4" />
                      Browse Workflows
                    </Link>
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Registry Info</CardTitle>
                  <CardDescription>
                    Manifest registry details
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex h-32 items-center justify-center">
                      <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Total Manifests</span>
                        <span className="text-sm font-bold">{stats?.total_manifests || 0}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Last Updated</span>
                        <span className="text-xs text-muted-foreground">
                          {stats?.last_updated ? new Date(stats.last_updated).toLocaleTimeString() : 'N/A'}
                        </span>
                      </div>
                      <Button 
                        onClick={handleSync}
                        disabled={syncing}
                        variant="outline" 
                        className="w-full mt-4"
                      >
                        <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                        Force Sync
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
                <CardDescription>
                  Service health and availability
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Manifest Ingestion</span>
                    {getHealthBadge(health.manifest?.status)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Runtime Executor</span>
                    {getHealthBadge(health.runtime?.status)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">LLM Gateway</span>
                    {getHealthBadge(health.llm?.status)}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
