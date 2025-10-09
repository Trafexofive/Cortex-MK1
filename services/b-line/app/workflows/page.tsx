"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Workflow, Play, Eye, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/client";

interface WorkflowManifest {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  steps?: any[];
  triggers?: {
    event?: string;
    schedule?: string;
  };
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<WorkflowManifest[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await api.manifests.listWorkflows();
      setWorkflows(data || []);
    } catch (error) {
      console.error("Failed to load workflows:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.manifests.sync();
      await loadWorkflows();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleViewWorkflow = (name: string) => {
    router.push(`/workflows/${encodeURIComponent(name)}`);
  };

  const stableWorkflows = workflows.filter(w => w.state === "stable");
  const unstableWorkflows = workflows.filter(w => w.state === "unstable");

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
                <h1 className="text-3xl font-bold tracking-tight">Workflows</h1>
                <p className="text-muted-foreground">
                  Multi-step orchestrations that coordinate agents and tools
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

            {/* Tabs */}
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList>
                <TabsTrigger value="all">
                  All ({workflows.length})
                </TabsTrigger>
                <TabsTrigger value="stable">
                  Stable ({stableWorkflows.length})
                </TabsTrigger>
                <TabsTrigger value="unstable">
                  Unstable ({unstableWorkflows.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {loading ? (
                  <div className="text-center py-12">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">Loading workflows...</p>
                  </div>
                ) : workflows.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center py-12">
                      <Workflow className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No Workflows Found</h3>
                      <p className="text-muted-foreground mb-4">
                        No workflow manifests have been ingested yet.
                      </p>
                      <Button onClick={handleSync} disabled={syncing}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                        Sync Manifests
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {workflows.map((workflow) => (
                      <Card key={workflow.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              <Workflow className="h-5 w-5 text-primary" />
                              <CardTitle className="text-lg">{workflow.name}</CardTitle>
                            </div>
                            <Badge variant={workflow.state === "stable" ? "default" : "secondary"}>
                              {workflow.state}
                            </Badge>
                          </div>
                          <CardDescription className="line-clamp-2">
                            {workflow.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Author:</span> {workflow.author || "Unknown"}
                            </div>
                            {workflow.version && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Version:</span> {workflow.version}
                              </div>
                            )}
                            {workflow.steps && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Steps:</span> {workflow.steps.length}
                              </div>
                            )}
                            {workflow.triggers && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Trigger:</span>{" "}
                                {workflow.triggers.event || workflow.triggers.schedule || "Manual"}
                              </div>
                            )}
                          </div>
                          <div className="mt-4 flex gap-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onClick={() => handleViewWorkflow(workflow.name)}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              disabled
                              title="Coming soon"
                            >
                              <Play className="mr-2 h-4 w-4" />
                              Execute
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="stable" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {stableWorkflows.map((workflow) => (
                    <Card key={workflow.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Workflow className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{workflow.name}</CardTitle>
                          </div>
                          <Badge>stable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {workflow.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {workflow.author || "Unknown"}
                          </div>
                          {workflow.steps && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Steps:</span> {workflow.steps.length}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewWorkflow(workflow.name)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            disabled
                            title="Coming soon"
                          >
                            <Play className="mr-2 h-4 w-4" />
                            Execute
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="unstable" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {unstableWorkflows.map((workflow) => (
                    <Card key={workflow.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Workflow className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{workflow.name}</CardTitle>
                          </div>
                          <Badge variant="secondary">unstable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {workflow.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {workflow.author || "Unknown"}
                          </div>
                          {workflow.steps && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Steps:</span> {workflow.steps.length}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewWorkflow(workflow.name)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            disabled
                            title="Coming soon"
                          >
                            <Play className="mr-2 h-4 w-4" />
                            Execute
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}
