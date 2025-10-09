"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Wrench, Play, Eye, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/client";

interface Tool {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  parameters?: Record<string, any>;
  returns?: {
    type?: string;
    description?: string;
  };
}

export default function ToolsPage() {
  const router = useRouter();
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const data = await api.manifests.listTools();
      setTools(data || []);
    } catch (error) {
      console.error("Failed to load tools:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.manifests.sync();
      await loadTools();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleViewTool = (name: string) => {
    router.push(`/tools/${encodeURIComponent(name)}`);
  };

  const stableTools = tools.filter(t => t.state === "stable");
  const unstableTools = tools.filter(t => t.state === "unstable");

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
                <h1 className="text-3xl font-bold tracking-tight">Tools</h1>
                <p className="text-muted-foreground">
                  Reusable functions that agents can use to perform actions
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
                  All ({tools.length})
                </TabsTrigger>
                <TabsTrigger value="stable">
                  Stable ({stableTools.length})
                </TabsTrigger>
                <TabsTrigger value="unstable">
                  Unstable ({unstableTools.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {loading ? (
                  <div className="text-center py-12">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">Loading tools...</p>
                  </div>
                ) : tools.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center py-12">
                      <Wrench className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No Tools Found</h3>
                      <p className="text-muted-foreground mb-4">
                        No tool manifests have been ingested yet.
                      </p>
                      <Button onClick={handleSync} disabled={syncing}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                        Sync Manifests
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {tools.map((tool) => (
                      <Card key={tool.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              <Wrench className="h-5 w-5 text-primary" />
                              <CardTitle className="text-lg">{tool.name}</CardTitle>
                            </div>
                            <Badge variant={tool.state === "stable" ? "default" : "secondary"}>
                              {tool.state}
                            </Badge>
                          </div>
                          <CardDescription className="line-clamp-2">
                            {tool.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Author:</span> {tool.author || "Unknown"}
                            </div>
                            {tool.version && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Version:</span> {tool.version}
                              </div>
                            )}
                            {tool.parameters && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Parameters:</span> {Object.keys(tool.parameters).length}
                              </div>
                            )}
                          </div>
                          <div className="mt-4 flex gap-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onClick={() => handleViewTool(tool.name)}
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
                  {stableTools.map((tool) => (
                    <Card key={tool.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Wrench className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{tool.name}</CardTitle>
                          </div>
                          <Badge>stable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {tool.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {tool.author || "Unknown"}
                          </div>
                          {tool.parameters && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Parameters:</span> {Object.keys(tool.parameters).length}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewTool(tool.name)}
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
                  {unstableTools.map((tool) => (
                    <Card key={tool.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Wrench className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{tool.name}</CardTitle>
                          </div>
                          <Badge variant="secondary">unstable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {tool.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {tool.author || "Unknown"}
                          </div>
                          {tool.parameters && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Parameters:</span> {Object.keys(tool.parameters).length}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewTool(tool.name)}
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
