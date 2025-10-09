"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Wrench, RefreshCw } from "lucide-react";
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
  implementation?: {
    type?: string;
    handler?: string;
  };
}

export default function ToolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [tool, setTool] = useState<Tool | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.name) {
      loadTool(params.name as string);
    }
  }, [params.name]);

  const loadTool = async (name: string) => {
    try {
      const data = await api.manifests.getTool(name);
      setTool(data);
    } catch (error) {
      console.error("Failed to load tool:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Tool not found</h2>
          <Button className="mt-4" onClick={() => router.push("/tools")}>
            Back to Tools
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => router.push("/tools")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Tools
            </Button>

            {/* Tool Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <Wrench className="h-10 w-10 text-primary" />
                  <div>
                    <h1 className="text-3xl font-bold tracking-tight">{tool.name}</h1>
                    {tool.version && (
                      <p className="text-sm text-muted-foreground">v{tool.version}</p>
                    )}
                  </div>
                </div>
                <p className="text-lg text-muted-foreground">{tool.summary}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant={tool.state === "stable" ? "default" : "secondary"} className="text-sm">
                  {tool.state}
                </Badge>
              </div>
            </div>

            <Separator />

            {/* Details Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-medium">Author</div>
                    <div className="text-sm text-muted-foreground">{tool.author || "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">State</div>
                    <div className="text-sm text-muted-foreground capitalize">{tool.state}</div>
                  </div>
                  {tool.version && (
                    <div>
                      <div className="text-sm font-medium">Version</div>
                      <div className="text-sm text-muted-foreground">{tool.version}</div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Implementation */}
              {tool.implementation && (
                <Card>
                  <CardHeader>
                    <CardTitle>Implementation</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {tool.implementation.type && (
                      <div>
                        <div className="text-sm font-medium">Type</div>
                        <div className="text-sm text-muted-foreground">{tool.implementation.type}</div>
                      </div>
                    )}
                    {tool.implementation.handler && (
                      <div>
                        <div className="text-sm font-medium">Handler</div>
                        <div className="text-sm text-muted-foreground font-mono text-xs">
                          {tool.implementation.handler}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Parameters */}
            {tool.parameters && Object.keys(tool.parameters).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Parameters</CardTitle>
                  <CardDescription>Input parameters accepted by this tool</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(tool.parameters).map(([key, value]: [string, any]) => (
                      <div key={key} className="border-l-2 border-primary/50 pl-4">
                        <div className="flex items-center gap-2">
                          <code className="text-sm font-semibold">{key}</code>
                          {value.required && (
                            <Badge variant="outline" className="text-xs">required</Badge>
                          )}
                        </div>
                        <div className="mt-1 text-sm text-muted-foreground">
                          {value.description || "No description"}
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          Type: <code>{value.type || "any"}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Returns */}
            {tool.returns && (
              <Card>
                <CardHeader>
                  <CardTitle>Returns</CardTitle>
                  <CardDescription>Output returned by this tool</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {tool.returns.type && (
                      <div>
                        <div className="text-sm font-medium">Type</div>
                        <code className="text-sm text-muted-foreground">{tool.returns.type}</code>
                      </div>
                    )}
                    {tool.returns.description && (
                      <div>
                        <div className="text-sm font-medium">Description</div>
                        <div className="text-sm text-muted-foreground">{tool.returns.description}</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button disabled title="Coming soon">
                  Execute Tool
                </Button>
                <Button variant="outline" disabled title="Coming soon">
                  Edit Manifest
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => loadTool(params.name as string)}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
