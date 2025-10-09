"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Server, Play, Eye, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/client";

interface Relic {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  deployment?: {
    type?: string;
    port?: number;
    protocol?: string;
  };
  import?: {
    agents?: string[];
    tools?: string[];
  };
}

export default function RelicsPage() {
  const router = useRouter();
  const [relics, setRelics] = useState<Relic[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadRelics();
  }, []);

  const loadRelics = async () => {
    try {
      const data = await api.manifests.listRelics();
      setRelics(data || []);
    } catch (error) {
      console.error("Failed to load relics:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.manifests.sync();
      await loadRelics();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleViewRelic = (name: string) => {
    router.push(`/relics/${encodeURIComponent(name)}`);
  };

  const stableRelics = relics.filter(r => r.state === "stable");
  const unstableRelics = relics.filter(r => r.state === "unstable");

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
                <h1 className="text-3xl font-bold tracking-tight">Relics</h1>
                <p className="text-muted-foreground">
                  Deployable services that expose agents as APIs or applications
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
                  All ({relics.length})
                </TabsTrigger>
                <TabsTrigger value="stable">
                  Stable ({stableRelics.length})
                </TabsTrigger>
                <TabsTrigger value="unstable">
                  Unstable ({unstableRelics.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {loading ? (
                  <div className="text-center py-12">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">Loading relics...</p>
                  </div>
                ) : relics.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center py-12">
                      <Server className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <h3 className="text-lg font-semibold mb-2">No Relics Found</h3>
                      <p className="text-muted-foreground mb-4">
                        No relic manifests have been ingested yet.
                      </p>
                      <Button onClick={handleSync} disabled={syncing}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                        Sync Manifests
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {relics.map((relic) => (
                      <Card key={relic.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-2">
                              <Server className="h-5 w-5 text-primary" />
                              <CardTitle className="text-lg">{relic.name}</CardTitle>
                            </div>
                            <Badge variant={relic.state === "stable" ? "default" : "secondary"}>
                              {relic.state}
                            </Badge>
                          </div>
                          <CardDescription className="line-clamp-2">
                            {relic.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Author:</span> {relic.author || "Unknown"}
                            </div>
                            {relic.version && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Version:</span> {relic.version}
                              </div>
                            )}
                            {relic.deployment?.type && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Type:</span> {relic.deployment.type}
                              </div>
                            )}
                            {relic.deployment?.port && (
                              <div className="text-sm text-muted-foreground">
                                <span className="font-medium">Port:</span> {relic.deployment.port}
                              </div>
                            )}
                          </div>
                          <div className="mt-4 flex gap-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="flex-1"
                              onClick={() => handleViewRelic(relic.name)}
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
                              Deploy
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
                  {stableRelics.map((relic) => (
                    <Card key={relic.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Server className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{relic.name}</CardTitle>
                          </div>
                          <Badge>stable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {relic.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {relic.author || "Unknown"}
                          </div>
                          {relic.deployment?.type && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Type:</span> {relic.deployment.type}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewRelic(relic.name)}
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
                            Deploy
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="unstable" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {unstableRelics.map((relic) => (
                    <Card key={relic.name} className="hover:border-primary/50 transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <Server className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">{relic.name}</CardTitle>
                          </div>
                          <Badge variant="secondary">unstable</Badge>
                        </div>
                        <CardDescription className="line-clamp-2">
                          {relic.summary || "No description"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Author:</span> {relic.author || "Unknown"}
                          </div>
                          {relic.deployment?.type && (
                            <div className="text-sm text-muted-foreground">
                              <span className="font-medium">Type:</span> {relic.deployment.type}
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="flex-1"
                            onClick={() => handleViewRelic(relic.name)}
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
                            Deploy
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
